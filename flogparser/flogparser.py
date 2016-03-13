import time
import sys
import threading
import signal
import traceback
import logging
import Queue

import tailer
import parser

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
        signal.signal(self.sig, self.original_handler)
        self.released.set()
        return True

def main(fn):
    logging.basicConfig(level=logging.DEBUG)

    with InterruptHandler() as h:
        try:
            logging.info("#### STARTING ####")
            tailqueue = Queue.Queue()
            producer = tailer.Tailer(fn,h.interrupted,tailqueue)
            consumer = parser.Parser(h.interrupted,tailqueue)
        
            producer.start()
            consumer.start()

            # Wait for SIGINT/TERM
            while not h.interrupted.is_set():
                time.sleep(0.5)

            logging.info("#### SHUTTING DOWN ####")
            producer.join()
            consumer.join()

        except Exception:
            logging.error(traceback.format_exc())
            sys.exit(1)
        finally:
            logging.info("#### FLOGPARSER TERMINATED ####")
        sys.exit(0)

if __name__ == "__main__":
    main('/tmp/foo')
