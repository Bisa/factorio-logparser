import Queue
import threading
import logging

import tailer

class Parser(threading.Thread):

    def __init__(self, stop_flag, tailqueue):
        super(Parser, self).__init__()
        self.stop_flag = stop_flag
        self.tailqueue = tailqueue

    def run(self):
        logging.info("#### PARSING: Inititated ####")
        while True:
           try:
               #TODO: something useful 8implement listeners?)
               print(self.tailqueue.get_nowait())
           except  Queue.Empty:
               # No more messages on queue, stop processing?
               if self.stop_flag.is_set():
                   logging.info("#### STOPPING PARSER ####")
                   break
               pass
