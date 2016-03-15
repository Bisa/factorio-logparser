import time
import sys
import threading
import signal
import traceback
import logging
import Queue
import imp
import os
import argparse

import flogparser

class InterruptHandler(object):
    def __init__(self, sig=signal.SIGINT):
        self.sig = sig
        
    def __enter__(self):
        self.interrupted = threading.Event()
        self.released = threading.Event()
        self.original_handler = signal.getsignal(self.sig)
        def handler(signum, frame):
            self.release()
            self.interrupted.set()
        signal.signal(self.sig, handler)
        return self
        
    def __exit__(self, type, value, tb):
        self.release()
        
    def release(self):
        if self.released.is_set():
            return False
        logging.info("#### SHUTTING DOWN ####")
        signal.signal(self.sig, self.original_handler)
        self.released.set()
        return True

def get_listener_modules(listenerfolder):
    listeners = []
    possiblemodules = os.listdir(listenerfolder)
    for folder in possiblemodules:
        location = os.path.join(listenerfolder, folder)
        if not os.path.isdir(location) or not "__init__.py" in os.listdir(location):
            continue
        info = imp.find_module("__init__", [location])
        listeners.append({"name": folder, "info": info})
    return listeners

def load_listener(listener):
    return imp.load_module("__init__", *listener["info"])

def main(options):
    logging.basicConfig(level=logging.DEBUG)

    with InterruptHandler() as h:
        try:
            logging.info("#### STARTING ####")

            tailqueue = Queue.Queue()
            tailer = flogparser.Tailer(options.logfile,h.interrupted,tailqueue)

            patterns = []
            # NetworkInputHandler.cpp
            networkpatterns = flogparser.Pattern("NetworkInputHandler\.cpp", None, True)
            networkpatterns.append_child(flogparser.Pattern("removing peer\\((?P<peer_id>\d+)\\) success\\(true\\)", "PEER_REMOVE"))
            networkpatterns.append_child(flogparser.Pattern("assigning playerIndex\\((?P<player_index>\d+)\\) to peer\\((?P<peer_id>\d+)\\)", "PEER_PLAYERINDEX"))
            networkpatterns.append_child(flogparser.Pattern("Multiplayer desynchronisation: crc test\\(CheckCRCHeuristic\\) failed for mapTick\\((?P<map_tick>\d+)\\) peer\\((?P<peer_id>\d+)\\) testCrc\\([^\\)]+\\) testCrcPeerID\\(0\\)", "PEER_DESYNC"))
            patterns.append(networkpatterns)
            # Router.cpp
            routerpatterns = flogparser.Pattern("Router\.cpp", None, True)
            routerpatterns.append_child(flogparser.Pattern("adding peer\\((?P<peer_id>\d+)\\) address\\((?P<peer_ip>([0-9]{1,3}\\.){3}[0-9]{1,3})\\:(?P<peer_port>[0-9]{1,5})\\)", "PEER_ADDED"))
            routerpatterns.append_child(flogparser.Pattern("Router state \\-\\> Disconnected$", "SERVER_STOP"))
            patterns.append(routerpatterns)
            # MultiplayerManager.cpp
            mppatterns = flogparser.Pattern("MultiplayerManager\.cpp", None, True)
            mppatterns.append_child(flogparser.Pattern("Received peer info for peer\\((?P<peer_id>\d+)\\) username\\((?P<username>.+)\\)\\.$", "PEER_USERNAME"))
            mppatterns.append_child(flogparser.Pattern("changing state from\\(CreatingGame\\) to\\(InGame\\)$", "SERVER_START"))
            mppatterns.append_child(flogparser.Pattern("Peer dropout for peer \\((?P<peer_id>\d+)\\) by peer \\(0\\) -- removing now", "PEER_REMOVE"))
            patterns.append(mppatterns)

            parser = flogparser.Parser(h.interrupted,tailqueue,patterns)

            for listener in get_listener_modules("./listeners"):
                parser.register_listener(load_listener(listener))
        
            parser.start()
            tailer.start()

            while not h.interrupted.is_set():
                time.sleep(1)

            tailer.join()
            parser.join()

        except Exception:
            logging.error(traceback.format_exc())
            sys.exit(1)
        finally:
            logging.info("#### FLOGPARSER TERMINATED ####")
        sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('logfile',
            help="absolute path to factorio-current.log")

    options = parser.parse_args()
    main(options)
