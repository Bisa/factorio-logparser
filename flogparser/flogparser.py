import Queue
import threading
import time
import tailhead
import logging

class Tailer(threading.Thread):
    def __init__(self, filename, stop_flag, tailqueue):
        super(Tailer, self).__init__()

        self.filename = filename
        self.stop_flag = stop_flag
        self.tailqueue = tailqueue

    def run(self):
        logging.info("#### TAILING: " + self.filename +  " ####")
        for line in tailhead.follow_path(self.filename):
            # Stop tailing
            if self.stop_flag.is_set():
                break
            # Enqueue lines or sleep till we have a new line
            if line is not None:
                self.tailqueue.put(line)
            else:
                time.sleep(0.5)

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
