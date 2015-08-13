#!/usr/bin/env python
import threading, Queue, subprocess
import re, json, argparse
import os, sys, signal
import time, datetime, pytz

class Server:

    def __init__(self):
        self.peers = {}
        self.info = {}

    def start(self, args):
        self.peers = {}
        self.info = {}

    def stop(self, args):
        pass

    def add_peer(self, args):
        """Add peer to server list of peers."""

        """
        Ensure the status report informs if the parser is started after
        Factorio has been started. Factorio will increment the peer id of each
        consecutive peer, starting with id 0 for the "server" itself.
        Since we do not register the server peer we can verify that the first
        peer added has id 1
        """
        if len(self.peers) == 0 and args['peer_id'] > 1:
            self.info['missing_peers'] = "The log parser needs to be started " \
                                         "before factorio, we've missed " \
                                         "registering some peers"

        if args['peer_id'] in self.peers:
            raise ValueError("Peer id ", args['peer_id'], " already exist, " \
                    "unable to add the same peer again!", args)

        """ Ensure we have the required ip:port for new peers """
        if 'peer_ip' not in args:
            raise ValueError("Missing peer ip for peer ", args['peer_id'], \
                    ", unable to add new peer!")
        if 'peer_port' not in args:
            raise ValueError("Missing peer port for peer ", args['peer_id'], \
                    ", unable to add new peer!")
        
        self.peers[args['peer_id']] = {
            'peer_ip': args['peer_ip'],
            'peer_port': args['peer_port'],
            'online': True,
            'desyncs': [],
            'connected': datetime.datetime.utcnow().replace(tzinfo = pytz.utc)
        }

    def remove_peer(self, args):
        """Remove peer from server list of peers."""
        if args['peer_id'] in self.peers:
            self.peers[args['peer_id']]['disconnected'] = \
                    datetime.datetime.utcnow().replace(tzinfo = pytz.utc)
            self.peers[args['peer_id']]['online'] = False

    def desync_peer(self, args):
        """Register a desync for specific peer."""
        if args['peer_id'] in self.peers:
            desync = datetime.datetime.utcnow().replace(tzinfo = pytz.utc)
            self.peers[args['peer_id']]['desyncs'].append(desync)

    def set_username(self, args):
        """Set username for a specific peer."""

        """Ignore the server which always has peer id 0"""
        if args['peer_id'] != 0:
            self.peers[args['peer_id']]['username'] = args['username']

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

def tail_forever(filename, queue, tailing):
    """Tail specified file forever, put read lines on queue."""
    if not os.access(filename, os.R_OK):
        print "Unable to read ", filename
        tailing[0] = False
    try:
        cmd = ['tail', '-F', '-n', '+1', filename]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        while 1:
            line = p.stdout.readline()
            queue.put(line)
            if not line:
                break
    except:
        tailing[0] = False

def signal_handler(signal, frame):
    print('Shutting down')
    sys.exit(0)

def report_status(outputfile, frequency, server, tailing):
    """Output JSON with current status/state with assigned frequency"""
    try:
        status = {
            'generated': datetime.datetime.utcnow().replace(tzinfo = pytz.utc),
            'peers': server.peers,
            'info': server.info
        }
        
        status_json = json.dumps(status, indent=1, sort_keys=True, separators=(',', ': '), cls=DateTimeEncoder) 
        status_file = open(outputfile, 'w')
        status_file.write(status_json)
        status_file.close()
        print status_json
    except Exception as e:
        # TODO: Handle exceptions?
        print "Error reporting status: ", e
    finally:
        if tailing[0]:
            threading.Timer(frequency, report_status, [outputfile, frequency, server, tailing]).start()

def main(options):
    server = Server()
    tailq = Queue.Queue()
    signal.signal(signal.SIGINT, signal_handler)
    tailing = [True]
    threading.Thread(target=tail_forever, args=(options.logfile, tailq,
        tailing)).start()
    report_status(options.outputfile, options.statusfrequency, server, tailing)

    regex = {}
    # NetworkInputHandler.cpp
    regex[0] = {}
    regex[0][0] = re.compile("NetworkInputHandler.cpp")
    regex[0]['removepeer'] = Processor("removing peer\\((?P<peer_id>\d+)\\) success\\(true\\)", server.remove_peer)
    regex[0]['desync_peer'] = Processor("Multiplayer desynchronisation: crc test\\(CheckCRCHeuristic\\) failed for mapTick\\((?P<map_tick>\d+)\\) peer\\((?P<peer_id>\d+)\\) testCrc\\([^\\)]+\\) testCrcPeerID\\(0\\)", server.desync_peer)
    # Router.cpp
    regex[1] = {}
    regex[1][0] = re.compile("Router.cpp")
    regex[1]['addingpeer'] = Processor("adding peer\\((?P<peer_id>\d+)\\) address\\((?P<peer_ip>([0-9]{1,3}\\.){3}[0-9]{1,3})\\:(?P<peer_port>[0-9]{1,5})\\)", server.add_peer)
    regex[1]['server_stop'] = Processor("Router state \\-\\> Disconnected$", server.stop)
    # MultiplayerManager.cpp
    regex[2] = {}
    regex[2][0] = re.compile("MultiplayerManager.cpp")
    regex[2]['set_username'] = Processor("Received peer info for peer\\((?P<peer_id>\d+)\\) username\\((?P<username>.+)\\)\\.$", server.set_username)
    regex[2]['server_start'] = Processor("changing state from\\(CreatingGame\\) to\\(InGame\\)$", server.start)
    regex[2]['removepeer_drop'] = Processor("Peer dropout for peer \\((?P<peer_id>\d+)\\) by peer \\(0\\) -- removing now", server.remove_peer)

    while tailing[0]:
        try:
            line = tailq.get_nowait()
            for group in regex.iterkeys():
                groupmatch = regex[group][0].search(line)
                if groupmatch:
                    for processor_id in regex[group].iterkeys():
                        """Skip the group identifier on index 0"""
                        if processor_id == 0:
                            continue
                        processor = regex[group][processor_id]
                        match = processor.pattern.search(line)
                        if match:
                            args = match.groupdict()
                            try:
                                args['peer_id'] = int(args['peer_id'])
                                args['peer_port'] = int(args['peer_port'])
                            except:
                                """
                                We expect most of our regex matches to find
                                a peer_id, the others can easily be dismissed
                                as exceptions and passed
                                """
                                pass
                            finally:
                                processor.action(args)
                                break
                    break

        except Queue.Empty:
            time.sleep(0.5)
        except Exception as e:
            print "Failed attempting to parse line: ", line
            print "Exception: ", e.message
        except:
            print "Something done goofed for real attempting to parse line: " \
                    , line

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('logfile',
            help="absolute path to factorio-current.log")
    parser.add_argument('-o', '--outputfile',
            help="absolute path to status output file")
    parser.add_argument('-f', '--statusfrequency', type=float,
            help="frequency in seconds for reporting status")

    options = parser.parse_args()
    sys.exit(main(options))

