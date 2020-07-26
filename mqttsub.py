import paho.mqtt.client as mqtt

class MyMQTTClass(mqtt.Client):

    def __init__(self, receiveMethod):
        self.receiveMethod=receiveMethod
        super().__init__()

    def on_connect(self, mqttc, obj, flags, rc):
        if rc == 0:
            self.connected = True  # set flag
            print("connected OK")
        else:
            print("Bad connection Returned code=", rc)
    
    def on_message(self, mqttc, obj, msg):
        self.receiveMethod(msg)

    def run(self, host, port, topic):
        print("host: ",host," port: ",port)
        self.connect(host, port, 60)
        self.subscribe(topic, 0)

        rc = 0
        while rc == 0:
            rc = self.loop()
        return rc

