import Queue
import threading
import time
import tailhead
import logging
import re

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

class Pattern():
    def __init__(self, regex, actionevent, pattern_group=False):
        self.regex = re.compile(regex)
        self.actionevent = actionevent
        if pattern_group:
            self.children = []        

    def append_child(self, child):
        self.children.append(child)

    def search(self, line):
        return self.regex.search(line)

class Parser(threading.Thread):

    def __init__(self, stop_flag, tailqueue,patterns):
        super(Parser, self).__init__()
        self.stop_flag = stop_flag
        self.tailqueue = tailqueue
        self.listeners = []
        self.patterns = patterns

    def run(self):
        logging.info("#### PARSING: Inititated ####")
        while not self.stop_flag.is_set():
            try:
                line = self.tailqueue.get_nowait()
                for pattern in self.patterns:
                    if pattern.search(line):
                        for child in pattern.children:
                            match = child.search(line)
                            if match:
                                print "Found match: ", match.groupdict(),
                                print " triggering: ", child.actionevent
                                for listener in self.listeners:
                                    listener.react(line)
            except Queue.Empty:
                time.sleep(0.5)

        logging.info("#### STOPPING PARSER ####")

    def register_listener(self, listener):
        self.listeners.append(listener)
