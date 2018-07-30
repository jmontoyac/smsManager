#!/usr/bin/env python3
from pyrebase import pyrebase
from twilio.rest import Client
from twilio.twiml.messaging_response import Body, Message, Redirect, MessagingResponse
from time import sleep
import config

def sendmsgresp(num,msg):
    if (num != ''):
        response = MessagingResponse()
        message = Message(to=num,
               from_="+12149970342",
               body=msg)
        response.append(message)
        response.redirect('https://demo.twilio.com/welcome/sms/')
        print(response)

def sendmsg(num,msg):
    if (num != ''):
       nums=num.split(',')
       for n in nums:
         client = Client(config.account_sid, config.auth_token)
         print("numero dispositivo: " + num)

         message = client.messages.create(
               to=n,
               messaging_service_sid="MG81df10e4450fcde193a378d76e104e28",
               body=msg)


fireb = pyrebase.initialize_app(config.firebaseConf)
db = fireb.database()

def stream_handler(message):
    print('event={m[event]}; path={m[path]}; data={m[data]}'
        .format(m=message))
    if (message["event"] == "put" and message["path"] == "/"):
      for command in message["data"]:
        print('data command: {d}'.format(d=command))
        data = message["data"][command]
        print('datos: {0}',data)
        for key,val in data.items():
          print(key, "=>", val)
        numero=data["number"]
        comando=data["command"]
        status=data["status"]
        print('comando:' + comando + 'status: ' + status)
        if (status == 'INITIAL'):
            sendmsg(numero, comando)
    elif (message["event"] == "put" and message["data"]):
        numero=message["data"]["number"]
        comando=message["data"]["command"]
        print('comando:' + comando)
        sendmsg(numero, comando)
        if (comando.endswith("lock")):
           sleep(3)
   
my_stream =db.child('Commands').stream(stream_handler)

# Run Stream Handler forever
while True:
    data = input("[{}] Type exit to disconnect: ".format('?'))
    if data.strip().lower() == 'exit':
        print('Stop Stream Handler')
        if my_stream: my_stream.close()
        break
