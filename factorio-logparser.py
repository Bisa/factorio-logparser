#!/usr/bin/env python
import threading
import Queue
import re
import subprocess
import sys
import signal
import time
import datetime
import pytz
import json
import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('logfile', help="absolute path to factorio-current.log")
parser.add_argument('-o', '--outputfile', help="absolute path to status output file")
parser.add_argument('-f', '--statusfrequency', type=float, help="frequency in seconds for reporting status")
options = parser.parse_args()

# TODO: Break out into separate packages/files?
class Server:

    peers = {}
    info = {}

    @staticmethod
    def start(args):
        Server.peers = {}

    @staticmethod
    def stop(args):
        Server.peers = {}

    @staticmethod
    def add_peer(args):
        # Ensure the status report informs if the parser is started after Factorio has been started.
        # Factorio will increment the peer id of each consecutive peer, starting with id 0 for the "server" itself.
        # Since we do not register the server peer we can verify that the first peer added has peer id 1
        if len(Server.peers) == 0 and args['peer_id'] > 1:
            Server.info['missing_peers'] = "The log parser needs to be started before factorio, we've missed registering some peers"

        if args['peer_id'] in Server.peers:
            raise ValueError("Peer id ", args['peer_id'], " already exist, unable to add the same peer again!", args)

        # Ensure we have the required ip:port for new peers
        if 'peer_ip' not in args:
            raise ValueError("Missing peer ip for peer ", args['peer_id'], ", unable to add new peer!")
        if 'peer_port' not in args:
            raise ValueError("Missing peer port for peer ", args['peer_id'], ", unable to add new peer!")
        
        Server.peers[args['peer_id']] = {
            'peer_ip': args['peer_ip'],
            'peer_port': args['peer_port'],
            'online': True,
            'connected': datetime.datetime.utcnow().replace(tzinfo = pytz.utc)
        }

    @staticmethod
    def remove_peer(args):
        if args['peer_id'] in Server.peers:
            Server.peers[args['peer_id']]['disconnected'] = datetime.datetime.utcnow().replace(tzinfo = pytz.utc)
            Server.peers[args['peer_id']]['online'] = False

    @staticmethod
    def set_username(args):
        #print "Setting username"
        if args['peer_id'] != 0: # Ignore the server peer
            Server.peers[args['peer_id']]['username'] = args['username']

class Processor:
    def __init__(self, pattern, action):
        self.pattern = re.compile(pattern)
        self.action = action

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            encoded_object = obj.isoformat()
        else:
            encoded_object =json.JSONEncoder.default(self, obj)
        return encoded_object

#tailq = Queue.Queue(maxsize=100) # buffer at most 100 lines
tailq = Queue.Queue() # TODO: Potential memory issue?

def tail_forever(fn):
    p = subprocess.Popen(['tail', '-F', filename], stdout=subprocess.PIPE)
    while 1:
        line = p.stdout.readline()
        tailq.put(line)
        if not line:
            break

def signal_handler(signal, frame):
    print('Shutting down')
    sys.exit(0)

def report_status():
    try:
        status = {
            'generated': datetime.datetime.utcnow().replace(tzinfo = pytz.utc),
            'peers': Server.peers,
            'info': Server.info
        }
        
        status_json = json.dumps(status, indent=1, sort_keys=True, separators=(',', ': '), cls=DateTimeEncoder) 
        status_file = open(options.outputfile, 'w')
        status_file.write(status_json)
        status_file.close()
        print status_json
    except Exception as e:
        # TODO: handle any file related exceptions when/if writing to disk
        # we really just want to keep reporting the status, no matter what for now
        print "Error reporting status: ", e
    except:
        print "Error reporting status! ", options
    finally:
        threading.Timer(options.statusfrequency, report_status).start()
    

signal.signal(signal.SIGINT, signal_handler)

filename = options.logfile
threading.Thread(target=tail_forever, args=(filename,)).start()
report_status()


utilregex = {}
utilregex['peer_id'] = re.compile("(?<=peer\()\d+(?=\))")

regex = {}

# Synchronizer.cpp
regex[0] = {}
regex[0][0] = re.compile("NetworkInputHandler.cpp")
regex[0]['removepeer'] = Processor("removing peer\\((?P<peer_id>\d+)\\) success\\(true\\)", Server.remove_peer)
# Router.cpp
regex[1] = {}
regex[1][0] = re.compile("Router.cpp")
regex[1]['addingpeer'] = Processor("adding peer\\((?P<peer_id>\d+)\\) address\\((?P<peer_ip>([0-9]{1,3}\\.){3}[0-9]{1,3})\\:(?P<peer_port>[0-9]{1,5})\\) sending connectionAccept\\(true\\)$", Server.add_peer)
regex[1]['server_stop'] = Processor("Router state \\-\\> Disconnected$", Server.stop)
# MultiplayerManager.cpp
regex[2] = {}
regex[2][0] = re.compile("MultiplayerManager.cpp")
regex[2]['set_username'] = Processor("Received peer info for peer\\((?P<peer_id>\d+)\\) username\\((?P<username>.+)\\)\\.$", Server.set_username)
regex[2]['server_start'] = Processor("changing state from\\(CreatingGame\\) to\\(InGame\\)$", Server.start)

while  1:
    try:
        line = tailq.get_nowait() # throws Queue.Empty if there are no lines to read
        for group in regex.iterkeys():
            groupmatch = regex[group][0].search(line)
            if groupmatch:
                for processor_id in regex[group].iterkeys():
                    # Skip the group identifier on index 0
                    if processor_id == 0:
                        continue
                    processor = regex[group][processor_id]
                    match = processor.pattern.search(line)
                    if match:
                        print "Parsing line: ", line, "Matched: ", match.groupdict()
                        # Convert known ints to int type
                        # TODO: break out into a more generic "convert all integer strings to int type"-method if
                        # we happen to run into more than the currently known integers
                        args = match.groupdict()
                        try:
                            args['peer_id'] = int(args['peer_id'])
                            args['peer_port'] = int(args['peer_port'])
                        except:
                            # We expect most of our regex matches to find a peer_id, the others can easily be dismissed
                            # as exceptions and passed
                            pass
                        finally:
                            #print "Processor args: ", args
                            processor.action(args)
                            break #processor_id
                break #group

    except Queue.Empty:
        # Nothing to report, the tail did not find any new lines to parse
        time.sleep(1)
    except Exception as e:
        print "Error! ", e, e.message
        print "Attempted to parse line: ", line
    except:
        print "Something done goofed for real!"
        print "Attempted to parse line: ", line

