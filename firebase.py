#!/usr/bin/env python3
from pyrebase import pyrebase
from twilio.rest import Client
from twilio.twiml.messaging_response import Body, Message, Redirect, MessagingResponse
from time import sleep
import Queue
import config
import pymongo
import persistence as p
import threading

# Variables definition
commandQueue = Queue.Queue()

# Class to hold a message
class message:
  destination = ""
  contents = ""
  status = "INITIAL"
  #timeout = config.SMS_RESPONSE_TIMEOUT
  retried_times = 1

# Execute when threading timer expires
def timer_expired():
  number = threading.currentThread().getName()
  print("Timer for " + number + " expired in main thread")
  # Check in DB if command was already answered
  command_record = p.getRecord(number)
  if (command_record.status == "ANSWERED"):
    # Do nothing
    print("Command already answered for number " + number)

  # If command in DB is still INITIAL, send again, put command again in FB
  # and increment retries counter, change status to RETRYING
  # If retries are reached, update command in FB with status FAILED
  if (command_record.status == "INITIAL"):
    p.updateStatus(number, "RETRYING")


  # if ANSWERED of FAILED, check for PENDING records for the same number

def sendmsgresp(num,msg):
    if (num != ''):
        response = MessagingResponse()
        message = Message(to=num,
               from_=config.smsGatewayNumber,
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
               config.messaging_service_sid,
               body=msg)


# Send message to SMS Gateway, do not check or change command message status
# status and retries counter are checked when timer expires only
def sendMessage(num,msg):
  if (num != ''):
    nums=num.split(',')
    for n in nums:
      client = Client(config.account_sid, config.auth_token)
      print("numero dispositivo: " + num)
      # Store command message object in DB
      m = message()
      m.destination = num
      m.contents = msg
      command_queue.put(m)
      p.storeCommand(m)

      timer = threading.Timer(config.SMS_RESPONSE_TIMEOUT, timer_expired)
      timer.setName(m.destination)
      timer.start()
      print("Timer started for message to: " + num)

       # Send message to twilio
       #message = client.messages.create(
             #to=n,
             #config.messaging_service_sid,
             #body=msg)





fireb = pyrebase.initialize_app(config.firebaseConf)
db = fireb.database()

def stream_handler(message):
    print('event={m[event]}; path={m[path]}; data={m[data]}'
        .format(m=message))

    # Add command to queue

    if (message["event"] == "put" and message["path"] == "/"):
      for command in message["data"]:
        #print('data command: {d}'.format(d=command))
        data = message["data"][command]
        #print('datos: {0}',data)
        for key,val in data.items():
          print(key, "=>", val)
        numero=data["number"]
        comando=data["command"]
        status=data["status"]
        print('comando:' + comando + 'status: ' + status)
        if (status == 'INITIAL' or status == 'RETRYING'):
            #sendmsg(numero, comando)
            sendMessage(numero, m,comando)

    elif (message["event"] == "put" and message["data"]):
        numero=message["data"]["number"]
        comando=message["data"]["command"]
        print('comando:' + comando)
        sendmsg(numero, comando)
        if (comando.endswith("lock")):
           sleep(3)
   
my_stream = db.child('Commands').stream(stream_handler)

# Run Stream Handler forever
while True:
    data = input("[{}] Type exit to disconnect: ".format('?'))
    if data.strip().lower() == 'exit':
        print('Stop Stream Handler')
        if my_stream: my_stream.close()
        break
