import time
import tailhead
import sys
import threading
import Queue
import signal
import traceback
import logging

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

def tail(fn, stop_flag, tailq):
    logging.info("#### TAILING: " + fn +  " ####")
    for line in tailhead.follow_path(fn):
        # Stop tailing
        if stop_flag.is_set():
            break
        # Enqueue lines or sleep till we have a new line
        if line is not None:
            tailq.put(line)
        else:
            time.sleep(0.5)

def parse(stop_flag, tailq):
    logging.info("#### PARSING: Inititated ####")
    while True:
       try:
           #TODO: Something useful
           print tailq.get_nowait()
       except  Queue.Empty:
           # No more messages on queue, stop processing?
           if stop_flag.is_set():
               break
           pass

def main(fn):
    logging.basicConfig(level=logging.DEBUG)

    with InterruptHandler() as h:
        try:
            logging.info("#### STARTING ####")
            tailq = Queue.Queue()
            tailer = threading.Thread(target=tail, args=(fn,h.interrupted,tailq,))
            parser = threading.Thread(target=parse, args=(h.interrupted,tailq,))
        
            tailer.start()
            parser.start()

            # Wait for SIGINT/TERM
            while not h.interrupted.is_set():
                time.sleep(0.5)

            logging.info("#### SHUTTING DOWN ####")
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
    


