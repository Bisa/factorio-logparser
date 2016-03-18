
class ActionEvent(object):
    def __init__(self, args):
        self.args = args
        pass

    def to_string(self):
        me = "Action Event\n"
        for key, value in self.args.iteritems():
           me = me + "({0}): {1}\n".format(key, value)
        return me


class PeerActionEvent(ActionEvent):
    def __init__(self, args):
        self.peer_id = args['peer_id']
        super(PeerActionEvent, self).__init__(args)
        pass


class PeerAdded(PeerActionEvent):
    def __init__(self, args):
        self.peer_ip = args['peer_ip']
        self.peer_port = args['peer_port']
        super(PeerAdded, self).__init__(args)
        pass

class PeerUserName(PeerActionEvent):
    def __init__(self, args):
        self.peer_username = args['username']
        super(PeerUserName, self).__init__(args)
        pass

class PeerRemoved(PeerActionEvent):
    def __init__(self, args):
        super(PeerRemoved, self).__init__(args)
        pass

class PeerDesynced(PeerActionEvent):
    def __init__(self, args):
        super(PeerDesynced, self).__init__(args)
        pass

class PeerPlayerIndex(PeerActionEvent):
    def __init__(self, args):
        super(PeerPlayerIndex, self).__init__(args)
        pass

class ServerStarted(ActionEvent):
    def __init__(self, args):
        pass

class ServerStopped(ActionEvent):
    def __init__(self, args):
        pass

