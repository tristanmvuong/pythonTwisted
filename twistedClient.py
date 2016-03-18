# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

from twisted.internet import reactor, protocol
from multiprocessing import Process, Lock
import time
import random

Cid = ""
stdlock = None
which = None

class EchoClient(protocol.Protocol):
    def connectionMade(self):
        global which
        if which == 1:
            lat = random.uniform(33.9,34.1)
            if lat >= 0:
                latSign = "+"
            else:
                latSign = "-"
            lon = random.uniform(117.8,118.1)
            if lon >= 0:
                lonSign = "+"
            else:
                lonSign = "-"
            self.transport.write("IAMAT " + Cid + " " + latSign + ("%.6f" % lat) 
                + lonSign + ("%.6f" % lon) + " " + ("%.9f" % time.time()))
        else:
            self.transport.write("WHATSAT " + "client2" + " 30 3")
    
    def dataReceived(self, data):
        stdlock.acquire()
        print data
        stdlock.release()
        self.transport.loseConnection()
        self.transport.abortConnection() 
    def connectionLost(self, reason):
        return

class EchoFactory(protocol.ClientFactory):
    protocol = EchoClient
    def clientConnectionFailed(self, connector, reason):
        print "Connection Failed"
        reactor.stop()
    
    def clientConnectionLost(self, connector, reason):
        reactor.stop()

def startClient(msg,lock,cid):
    global which
    which = msg
    global Cid
    Cid = cid
    global stdlock
    stdlock = lock
    f = EchoFactory()
    portList = random.sample([8000, 8001, 8002, 8003, 8004], 1)
    port = portList[0]
    reactor.connectTCP("localhost", port, f)
    reactor.run()

def main():
    lock = Lock()
    clientId = []
    count = 2 
    while count > 0:
        clientId.append("client" + str(count))
        count = count - 1

    which = 1
    processList = []
    for CID in clientId:
        p = Process(target=startClient, args=(which,lock,CID,))
        p.start()
        processList.append(p)
        which = 2

# this only runs if the module was *not* imported
if __name__ == '__main__':
    main()
