import time
import sys
import threading
import signal
import traceback
import logging
import Queue
import imp
import os

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

PluginFolder = "./plugins"
MainModule = "__init__"

def getPlugins():
    plugins = []
    possibleplugins = os.listdir(PluginFolder)
    for i in possibleplugins:
        location = os.path.join(PluginFolder, i)
        if not os.path.isdir(location) or not MainModule + ".py" in os.listdir(location):
            continue
        info = imp.find_module(MainModule, [location])
        plugins.append({"name": i, "info": info})
    return plugins

def loadPlugin(plugin):
    return imp.load_module(MainModule, *plugin["info"])

def main(fn):
    logging.basicConfig(level=logging.DEBUG)

    with InterruptHandler() as h:
        try:
            logging.info("#### STARTING ####")
            tailqueue = Queue.Queue()
            tailer = flogparser.Tailer(fn,h.interrupted,tailqueue)
            parser = flogparser.Parser(h.interrupted,tailqueue)

            for plugin in getPlugins():
                parser.register_plugin(loadPlugin(plugin))
        
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
    main('/tmp/foo')
