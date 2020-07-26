import json
import mqttsub
import paho.mqtt.client as mqtt
import wx 
import argparse
import threading
from threading import Thread

class CoinType():
    CROSS="x"
    CIRCLE="o"

    def asString(coinType):
        if (coinType==CoinType.CROSS):
            return "Cross"
        else:
            return "Circle"

class Coin():

    def __init__(self, station, coinType):
        self.station=station
        self.coinType=coinType
        self.colorID=wx.Colour(0,0,0)

    def draw(self, dc): 
        color = self.colorID
        dc.SetBrush(wx.Brush(color, wx.BRUSHSTYLE_TRANSPARENT)) 
        dc.DrawCircle(self.station.x, self.station.y, 15)
        x=self.station.x; y=self.station.y
        if (self.coinType==CoinType.CROSS):
            dc.DrawLine(x-10,y-10,x+10,y+10)
            dc.DrawLine(x-10,y+10,x+10,y-10)

    def moveToStation(self, station):
        self.station.removeCoin()
        self.station=station
        self.station.setCoin(self)

class Station():

    def __init__(self, key, x, y):
        self.key=key
        self.x=x
        self.y=y
        self.colorID=wx.Colour(0,0,0)
        self.size=25 #distance to center
       
    def removeCoin(self):
        del(self.coin)

    def setCoin(self, coin):
        self.coin=coin

    def isOnField(self):
        if self.key[:1]=="x" or self.key[:1]=="o":
            return False
        return True

    def draw(self, dc): 
        if hasattr(self, 'coin'):
            self.coin.draw(dc)
    
    def isHit(self, x, y):
        if abs(x-self.x)<self.size and abs(y-self.y)<self.size:
            return True
        return False
    
    def isEmpty(self):
        return not hasattr(self, 'coin')

    def containsCoinType(self, coinType):
        if self.isEmpty():
            return False
        if self.coin.coinType==coinType:
            return True
        return False

class TicTacToe:

    graph =  { 'x1': [(75,125)],
        'x2': [(25,150)],
        'x3': [(75,175)],
        'x4': [(25,200)],
        'x5': [(75,225)],
        '11': [(175,125)],
        '11': [(175,125)],
        '12': [(175,175)],
        '12': [(175,175)],
        '23': [(225,225)],
        '23': [(225,225)],
        '13': [(175,225)],
        '13': [(175,225)],
        '21': [(225,125)],
        '22': [(225,175)],
        '31': [(275,125)],
        '32': [(275,175)],
        '33': [(275,225)],
        'o1': [(375,125)],
        'o2': [(425,150)],
        'o3': [(375,175)],
        'o4': [(425,200)],
        'o5': [(375,225)], 
        }
    
    possibleWin = [{"11", "12", "13"},
        {"21", "22", "23"},
        {"31", "32", "33"},
        {"11", "21", "31"},
        {"12", "22", "32"},
        {"13", "23", "33"},
        {"11", "22", "33"},
        {"13", "22", "31"},
        ]

    def __init__(self):
    # Schüler To Do initialisiere alle Stations mit key, x, y (x,y Position auf dem Bildschirm)
        self.stations=[]
        for key in self.graph:
            x,y=self.graph[key][0]
            station=Station(key,x,y)
            self.stations.append(station)
            if not station.isOnField():
                coinType=key[:1]
                coin=Coin(station, coinType)
                station.setCoin(coin)

    def draw(self, dc): 
        for row in range(2):
            dc.DrawLine(150,150+row*50,300,150+row*50)
        for column in range(2):
            dc.DrawLine(200+column*50,100,200+column*50,250)        
        for station in self.stations:
            station.draw(dc)
 
    def findStationKeyOnField (self, x,y):
        for station in self.stations:
            if station.isHit(x, y)==True and station.isOnField()==True:
                return station.key
        return ""

    def getStationWithUnusedCoin(self, coinType):
        for station in self.stations:
            if not station.isOnField():
                if station.containsCoinType(coinType):
                    return station
        assert("findStationWithUnusedCoin() Error")   

    def getStation(self, stationKey):
        for station in self.stations:
            if station.key==stationKey:
                return station
        assert("getStation() Error")
      
    def isWinner(self, coinType):
        win = False
        for toll in (self.possibleWin):
            if win == False:
                win = True
                for key in toll:
                    station = self.getStation(key)
                    if station.containsCoinType(coinType) == False:
                        win = False
        if win == True:
            print("the winner is ", CoinType.asString(coinType) )    
        return win
    
    def isFull (self):
        for station in self.stations:
            if station.isOnField():
                if station.isEmpty():
                    return False
        return True

class GameFrame(wx.Frame): 
            
    def __init__(self, parent, title, size, pos): 
        super(GameFrame, self).__init__(parent, title = title,size = size, pos = pos)  
        self.board = TicTacToe()
        self.initUI() 
        self.activePlayer=CoinType.CROSS
        self.mqtt = mqttsub.MyMQTTClass(self.receiveMQTT)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.MouseDown)
        self.topic = topic
        self.text = ""
        mqttThread = threading.Thread(target=self.mqtt.run, args=(hostname, port, topic)) 
        mqttThread.start()
     
    def initUI(self): 
        self.Show(True)

    def OnPaint(self, e):
        dc = wx.PaintDC(self)   
        brush = wx.Brush("white")  #Background color
        dc.SetBackground(brush)  
        dc.Clear() 
        self.board.draw(dc)
        self.writeText(dc)

    def receiveMQTT (self, mqttString):
        print("receiveMQTT(): Topic: ",mqttString.topic)
        payload = mqttString.payload.decode('utf-8')
        #print("Payload: ",payload)
        data=json.loads(payload)
        #print(data["stationFrom"])
        #print (data["stationTo"])
        #if self.activePlayer == my_type:
        stationTo = self.board.getStation(data["stationTo"])
        stationFrom = self.board.getStation(data["stationFrom"])
        if not stationFrom.isEmpty():
            stationFrom.coin.moveToStation(stationTo)
        #print ("stationTo = ", stationTo.key)
        #if stationTo.isEmpty()==True:                                       # steine werden verschoben

        if self.isEndOfGame():
            if self.board.isFull()== True:
                self.text = "The game ends draw"
            else:
                self.text = "The Winner is " + CoinType.asString(self.activePlayer)
        self.nextTurn()
        self.Update() 
        self.Hide()
        self.Show()


    def writeText(self, dc):
        #write Text TODO Exercise 2
        dc.DrawText(self.text,50,300)

    def isEndOfGame(self):
        if self.board.isWinner(my_type)==True or self.board.isWinner(other_type)==True:
            return True
        if self.board.isFull()== True:
            return True
        return False

    def MouseDown (self, e):
        if self.isEndOfGame() or not my_type == self.activePlayer:
            return
        x, y = e.GetPosition()
        stationKey= self.board.findStationKeyOnField(x,y)
        if (stationKey==""):
            return
        stationTo = self.board.getStation(stationKey) 
        if stationTo.isEmpty()==True:
            stationFrom=self.board.getStationWithUnusedCoin(self.activePlayer)
            print("stationFrom",stationFrom.key)
            print("stationTo", stationTo.key)
            myData = {}
            myData["stationFrom"]=stationFrom.key
            myData["stationTo"]=stationTo.key
            mqttString = json.dumps(myData)
            print("mousedown mqttstring erzeugt")
            self.mqtt.publish(self.topic, mqttString)
            
    def nextTurn(self):
        if self.activePlayer==CoinType.CROSS:
            self.activePlayer=CoinType.CIRCLE
            if not self.isEndOfGame():
                self.text = "its turn of " + CoinType.asString(self.activePlayer)
        else:
            self.activePlayer=CoinType.CROSS
            if not self.isEndOfGame():
                self.text = "its turn of " + CoinType.asString(self.activePlayer)
def main():
    app = wx.App() 
    startPosition=wx.Point(50,50)
    GameFrame(None,'Tic Tac Toe', size=(500,500), pos=startPosition) 
    app.MainLoop()

if __name__ == "__main__":
   
    parser = argparse.ArgumentParser(description = 'Parameter of the Game')
    parser.add_argument('-host', help='choose MQTT server hostname')
    parser.add_argument('-p', help='choose Port of MQTT server')
    parser.add_argument('-t', help='choose Topc of MQTT subscription')
    args = parser.parse_args()
    #hostname = "localhost"
    #hostname="broker.hivemq.com" #hostname MQTT Broker
    hostname="broker.hivemq.com"  #3.120.25.91"
    port=1883
    topic = "/game/tictactoe"
    

    if args.host:
        hostname = args.host
    if args.p:
        port=args.p
    if args.t:
        topic=args.t
    
    print ("-h=hostname:{0} -p=port:{1} -t=mqttTopic:{2}:".format(hostname, port, topic))

    my_type= input("choose player (x/o): ")
    
    if my_type == CoinType.CROSS:
        print ("my player is cross")
        other_type = CoinType.CIRCLE
    
    elif my_type == CoinType.CIRCLE:
        print ("my type is circle")
        other_type = CoinType.CROSS
    
    if not my_type == CoinType.CROSS and not my_type == CoinType.CIRCLE:
        print("options are x or o please restart")
        exit()

    main()
