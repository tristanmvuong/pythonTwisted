
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

from twisted.internet import reactor, protocol
from multiprocessing import Process, Lock
import time
import urllib2
import datetime
import json

sid = "test"
ports = None
locations = None
client = None
msgCount = None
lock = None
f = None
triple = None
processList = None
flooding = None

class EchoClient(protocol.Protocol):
    def connectionMade(self):
        global client
        global locations
        global msgCount
        global sid
        value = locations[client]
        propagate = "AT " + value[0] + " " + value[1] + " " + client + " " \
            + value[2] + " " + value[3] + " " + str(msgCount)
        fp = open('./' + sid + '.txt', 'a') 
        timeNow=str(datetime.datetime.now()).split('.')[0]
        fp.write(timeNow + " " + propagate + " " + "\n")
        self.transport.write(propagate)
    
    def dataReceived(self, data):
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

def flood(trio, server):
    global locations
    global client 
    global msgCount
    global sid
    locations = trio[0]
    client = trio[1]
    msgCount = trio[2] 
    sid = trio[3]
    f = EchoFactory()
    reactor.connectTCP("localhost", server, f)
    reactor.run()

class Echo(protocol.Protocol):
    def dataReceived(self, data):
        place = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?"
        apiKey = "AIzaSyC0YDuLdR4VPwUoqrFm1MERGC8s0invuek" 
        global locations
        global msgCount
        global client
        global processList
        global sid
        global flooding
        bad = 0;
        badResponse = "? " + data
        fp = open('./' + sid + '.txt', 'a')
        fp.write(str(datetime.datetime.now()).split('.')[0] + " " + data +\
            "\n")
        parse = []
        item = ""
        for c in data:
            if c in (" ","\t","\f","\r","\v","\n"):
                if item != "":
                    parse.append(item)
                    item = ""
            else:
                item = item + c
        if item != "":
            parse.append(item)
        if len(parse) == 4:
            if parse[0] == "IAMAT":
                coord = ""
                count = 0
                for a in parse[2]:
                    if a in ("+","-"): 
                        if coord != "":
                            if count >= 1:
                                bad = 1
                                self.transport.write(badResponse)
                            try:
                                float(coord)
                            except ValueError:
                                bad = 1
                                self.transport.write(badResponse)
                            coord = ""
                            count = count + 1
                    else:
                        coord = coord + a
                try:
                    float(coord)
                except ValueError:
                    bad = 1
                    self.transport.write(badResponse)

                try:
                    float(parse[3])
                except ValueError:
                    bad = 1
                    self.transport.write(badResponse)
                clientTime = float(parse[3]) 
                serverTime = time.time()
                diffTime = serverTime - clientTime
                diffSign = ""
                if diffTime >= 0:
                    diffSign = "+"
                timediff = diffSign + ("%.9f" % diffTime)
                response = "AT " + sid + " " + timediff + " " + parse[1] + " "\
                    + parse[2] + " " + parse[3]
                timeNow=str(datetime.datetime.now()).split('.')[0]
                fp.write(timeNow + " " + response + "\n")
                self.transport.write(response)

                locations[parse[1]] = (sid, timediff, parse[2], parse[3])
                client = parse[1]

                msgCount = 1
                flooding[client] = msgCount

                triple = (locations, client, msgCount, sid)
                if sid in ("Alford", "Bolden"):
                    p = Process(target=flood, args=(triple,ports["Parker"],))
                    processList.append((p,client))
                    p.start()
                    p = Process(target=flood, args=(triple,ports["Powell"],))
                    processList.append((p,client))
                    p.start()                    
                elif sid == "Hamilton":
                    p = Process(target=flood, args=(triple,ports["Parker"],))
                    processList.append((p,client))
                    p.start()
                elif sid == "Parker":
                    for proc in processList:
                        if proc[1] == client:
                            proc[0].terminate()
                    p = Process(target=flood, args=(triple,ports["Bolden"],))
                    processList.append((p,client))
                    p.start()
                    p = Process(target=flood, args=(triple,ports["Hamilton"],))
                    processList.append((p,client))
                    p.start()
                    p = Process(target=flood, args=(triple,ports["Alford"],))
                    processList.append((p,client))
                    p.start()
                else:
                    p = Process(target=flood, args=(triple,ports["Bolden"],))
                    processList.append((p,client))
                    p.start()
                    p = Process(target=flood, args=(triple,ports["Alford"],))
                    processList.append((p,client))
                    p.start()
            else:
                if parse[0] == "WHATSAT":
                    try:
                        int(parse[2])
                        int(parse[3])
                    except ValueError:
                        bad = 1
                        self.transport.write(badResponse)
                    radi = int(parse[2])
                    items = int(parse[3])
                    if radi < 0 or radi > 50 or items < 0 or items > 20:
                        bad = 1
                        self.transport.write(badResponse + "\n")
                    else:
                        if parse[1] in locations:
                            value = locations[parse[1]]
                            lat = ""
                            lon = ""
                            mark = 0
                            for c in value[2]:
                                if c in ("+","-"):
                                    if mark == 0:
                                        if c == "-":
                                            lat = "-"
                                        mark = 1
                                    else:
                                        if c == "-":
                                            lon = "-"
                                        mark = 2
                                else:
                                    if mark == 1:
                                        lat = lat + c
                                    else:
                                        lon = lon + c
                            #place is url, apiKey is key
                            loc = lat + "," + lon
                            nearbyRadius = str(radi)
                            url = place + "location=" + loc + "&" + "radius=" \
                                + nearbyRadius + "&" + "key=" + apiKey
                            response = urllib2.urlopen(url)
                            data = json.load(response)
                            while len(data["results"]) > items:
                                (data["results"]).pop()
                            data = json.dumps(data,indent=4) + "\n\n"
                            anotherResponse = "AT " + value[0] + " " + value[1]\
                                + " " + parse[1] + " " + value[2] + " " +\
                                value[3] + "\n" + data 
                            timeNow=str(datetime.datetime.now()).split('.')[0] 
                            fp.write(timeNow + " " + anotherResponse + "\n")
                            self.transport.write(anotherResponse)
                        else:
                            bad = 1
                            self.transport.write(badResponse)
                else:
                    bad = 1
                    self.transport.write(badResponse)
        else:
            if len(parse) == 7 and parse[0] == "AT":
                lock.acquire()
                lock.release()
                coord = ""
                count = 0
                for a in parse[4]:
                    if a in ("+","-"): 
                        if coord != "":
                            if count >= 1:
                                bad = 1
                                self.transport.write(badResponse)
                            try:
                                float(coord)
                            except ValueError:
                                bad = 1
                                self.transport.write(badResponse)
                            coord = ""
                            count = count + 1
                    else:
                        coord = coord + a
                try:
                    float(coord)
                except ValueError:
                    bad = 1
                    self.transport.write(badResponse)

                try:
                    float(parse[5])
                except ValueError:
                    bad = 1
                    self.transport.write(badResponse)

                if parse[3] not in locations:
                    locations[parse[3]] = [parse[1], parse[2],parse[4],
                        parse[5]]
                else:
                    if float((locations[parse[3]])[3]) < float(parse[5]):
                        locations[parse[3]] = [parse[1], parse[2],
                             parse[4], parse[5]]
 
                client = parse[3]
                msgCount = int(parse[6]) + 1
                flooding[client] = msgCount

                if flooding[client] == 4:
                    for proc in processList:
                        if proc[1] == client:
                            proc[0].terminate()
                    return
                
                triple = (locations,client,msgCount,sid)
                if sid in ("Alford", "Bolden"):
                    #lock.acquire()
                    for proc in processList:
                        if proc[1] == client:
                            proc[0].terminate()
                    p = Process(target=flood, args=(triple,ports["Parker"],))
                    processList.append((p,client))
                    p.start()
                    p = Process(target=flood, args=(triple,ports["Powell"],))
                    processList.append((p,client))
                    p.start()                    
                    #lock.release()
                elif sid == "Hamilton":
                    #lock.acquire()
                    for proc in processList:
                        if proc[1] == client:
                            proc[0].terminate()
                    p = Process(target=flood, args=(triple,ports["Parker"],))
                    processList.append((p,client))
                    p.start()
                    #lock.release()
                elif sid == "Parker":
                    #lock.acquire()
                    for proc in processList:
                        if proc[1] == client:
                            proc[0].terminate()
                    p = Process(target=flood, args=(triple,ports["Bolden"],))
                    processList.append((p,client))
                    p.start()
                    p = Process(target=flood, args=(triple,ports["Hamilton"],))
                    processList.append((p,client))
                    p.start()
                    p = Process(target=flood, args=(triple,ports["Alford"],))
                    processList.append((p,client))
                    p.start()
                    #lock.release()
                else:
                    #lock.acquire()
                    for proc in processList:
                        if proc[1] == client:
                            proc[0].terminate()
                    p = Process(target=flood, args=(triple,ports["Bolden"],))
                    processList.append((p,client)) 
                    p.start()
                    p = Process(target=flood, args=(triple,ports["Alford"],))
                    processList.append((p,client))
                    p.start()
                    #lock.release()
                self.transport.write("Received")
            else:
                bad = 1
                self.transport.write(badResponse)
        if bad == 1:
            timeNow=str(datetime.datetime.now()).split('.')[0]
            fp.write(timeNow + " " + badResponse + "\n")
        fp.close()

def startServer(lo,ID,portNum):
    global f
    f = EchoFactory()
    global lock
    lock = lo
    global sid
    sid = ID
    global ports
    ports = {"Alford": 8000, "Parker": 8001, "Powell": 8002,
        "Hamilton": 8003, "Bolden": 8004}
    global locations
    locations = {}
    global processList
    processList = []
    global flooding
    flooding = {}
    factory = protocol.ServerFactory()
    factory.protocol = Echo
    reactor.listenTCP(portNum,factory)
    reactor.run()

def main():
    serverId = ["Alford", "Parker", "Powell", "Hamilton", "Bolden"]
    serverPorts = [8000, 8001, 8002, 8003, 8004]
    lock = Lock()
    for SID,pn in zip(serverId, serverPorts):
         p = Process(target=startServer, args=(lock,SID,pn,))
         p.start()


# this only runs if the module was *not* imported
if __name__ == '__main__':
    main()
