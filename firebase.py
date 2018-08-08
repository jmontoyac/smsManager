#!/usr/bin/env python3
from pyrebase import pyrebase
from twilio.rest import Client
from twilio.twiml.messaging_response import Body, Message, Redirect, MessagingResponse
from time import sleep
import config
import pymongo
import persistence as p
import threading
import uuid
import queue

# Variables definition
commandQueue = queue.Queue()

# Class to hold a message
class mensaje_class:
  destination = ""
  contents = ""
  status = "INITIAL"
  retried_times = 1
  command_id = ""

# Execute when threading toimer expires
def timer_expired():
  id = threading.currentThread().getName()
  status = p.getStatus(id)
  retries = p.getRetries(id)
  number = p.getDestination(id)
  print("Timer " + id + " expired in main thread")
  print("command Status in timer expired: " + status)
  print("command retries in timer expired: " + str(retries))
  if (status == "ANSWERED"): 
    print ("Command was answered and updated in FB, delete record from data base: ")
    p.delete_record(id)
    # Look for commands in PENDING status for the same number
    pending = getPendingByNumber(number)
    print(pending)
    if (pending.count > 0):
      for x in pending:
        pendingId = x["command_id"]
      p.updateStatus(pendingId, "SENT")
      print("Sending pending command for: number")
      timer = threading.Timer(config.SMS_RESPONSE_TIMEOUT, timer_expired)
      timer.setName(id)
      timer.start()

  elif (status == "SENT"):
    print("Command not yet answered")
    if(retries <= config.SMS_RETRIES):
      retries += 1
      p.updateRetries(id, retries)
      print("Send command again, attempt #: " + str(retries))
      timer = threading.Timer(config.SMS_RESPONSE_TIMEOUT, timer_expired)
      timer.setName(id)
      timer.start()
    else:
      print("Message retries reached, answer to FB with FAILED status")
      p.updateStatus(id, "FAILED")
      p.delete_record(id)
      # Update status FAILED on Firebase, then delete the record
      # FB update with FAILED status


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
               messaging_service_sid = config.messaging_service_sid,
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
      m = mensaje_class()
      m.destination = num
      m.contents = msg
      m.status = "SENT"
      m.command_id = str(uuid.uuid4())
      #command_queue.put(m)
      p.storeCommand(m)

      # Send message to twilio
       #message = client.messages.create(
             #to=n,
             #messaging_service_sid = config.messaging_service_sid,
             #body=msg)

      timer = threading.Timer(config.SMS_RESPONSE_TIMEOUT, timer_expired)
      timer.setName(m.destination)
      timer.start()
      print("Timer started for message to: " + num)

       
# Initialize Firebase connection
fireb = pyrebase.initialize_app(config.firebaseConf)
db = fireb.database()

def stream_handler(message):
    print('event={m[event]}; path={m[path]}; data={m[data]}'
        .format(m=message))

    if (message["event"] == "put" and message["path"] == "/"):
      for command in message["data"]:
        data = message["data"][command]
        for key,val in data.items():
          print(key, "=>", val)
        numero=data["number"]
        comando=data["command"]
        status=data["status"]
        msg=mensaje_class()
        msg.destination = str(numero)
        msg.contents = comando
        msg.command_id = str(uuid.uuid4())
        print('comando:' + comando + 'status: ' + status)
        # if number found in db, create new record wuth command and status = PENDING
        # else add command to queue
        record = p.getRecordByNumber(msg.destination)
        if (record.count() > 0):
          print("Storing PENDING command for number: " + msg.destination)
          msg.status = "PENDING"
          p.storeCommand(msg)
        elif (status == 'INITIAL'):
          sendMessage(numero, comando)

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
