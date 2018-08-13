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
  contents = "DEFAULT"
  status = "INITIAL"
  retried_times = 1
  command_id = ""
  firebase_key = ""

# Execute when threading toimer expires
def timer_expired():
  print("Timer expired")
  id = threading.currentThread().getName()
  status = p.getStatus(id)
  retries = p.getRetries(id)
  number = p.getDestination(id)
  print("For command id: " + str(id))
  print ("For number: " + number)
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
      print("Sending pending command for: " +number)
      sendToGateway(p.getDestination(pendingId), p.getMessageById(pendingId))
      timer = threading.Timer(config.SMS_RESPONSE_TIMEOUT, timer_expired)
      timer.setName(pendingId)
      timer.start()

  elif (status == "SENT"):
    print("Command not yet answered")
    if(retries <= config.SMS_RETRIES):
      retries += 1
      p.updateRetries(id, retries)
      print("Send command again, attempt #: " + str(retries))
      sendToGateway(p.getDestination(id), p.getMessageById(id))
      timer = threading.Timer(config.SMS_RESPONSE_TIMEOUT, timer_expired)
      timer.setName(id)
      timer.start()
    else:
      print("Message retries reached, answer to FB with FAILED status")
      p.updateStatus(id, "FAILED")
      
      # Update status FAILED on Firebase, then delete the record
      data = {"response": "No answer, max retries reached",
              "status": "FAILED"}
      update_firebase(p.getFirebase_key(id), data)
      p.delete_record(id)

      # Look for commands in PENDING status for the same number
      pending = p.getPendingByNumber(number)
      print(pending)
      if (pending.count > 0):
        for x in pending:
          pendingId = x["command_id"]
        p.updateStatus(pendingId, "SENT")
        print("Sending pending command for: " +number)
        sendToGateway(p.getDestination(pendingId), p.getMessageById(pendingId))
        timer = threading.Timer(config.SMS_RESPONSE_TIMEOUT, timer_expired)
        timer.setName(pendingId)
        timer.start()

def sendmsgresp(num,msg):
    if (num != ''):
        response = MessagingResponse()
        message = Message(to=num,
               from_=config.smsGatewayNumber,
               body=msg)
        response.append(message)
        response.redirect('https://demo.twilio.com/welcome/sms/')
        print(response)

# Update Firebase with new status
def update_firebase(firebase_key, data):
    db.child("Commands").child(firebase_key).update(data)


# Send the SMS to message gateway
def sendToGateway(number, message):
  client = Client(config.account_sid, config.auth_token)
  message = client.messages.create(
          to=number,
          messaging_service_sid = config.messaging_service_sid,
          body=message)

# This method sends the message to a string of numbers
def sendmsg(num, mensaje, firebase_key):
    if (num != ''):
       nums=num.split(',')
       for n in nums:
         print("numero dispositivo: " + num)
         m=mensaje_class()
         m.destination = str(n)
         m.contents = mensaje
         m.status="SENT"
         m.command_id = str(uuid.uuid4())
         m.firebase_key = firebase_key
         p.storeCommand(m)
         sendToGateway(n, mensaje)
         
         timer = threading.Timer(config.SMS_RESPONSE_TIMEOUT, timer_expired)
         timer.setName(m.command_id)
         timer.start()
         print("sendmsg::Timer started for message to: " + num)


# Send message to SMS Gateway, do not check or change command message status
# status and retries counter are checked when timer expires only
def sendMessage(num,msg,firebase_key):
  if (num != ''):
    nums=num.split(',')
    for n in nums:
      print("numero dispositivo: " + num)
      # Store command message object in DB
      m = mensaje_class()
      m.destination = num
      m.contents = msg
      m.status = "SENT"
      m.command_id = str(uuid.uuid4())
      m.firebase_key = firebase_key

      p.storeCommand(m)
      sendToGateway(n, msg)

      timer = threading.Timer(config.SMS_RESPONSE_TIMEOUT, timer_expired)
      timer.setName(m.command_id)
      timer.start()
      print("sendMessage::Timer started for message to: " + num)

# This method sends the alert to a tracker device
def sendAlert(num, mensaje):
    print("ALERT sent to number: " + num)
    sendToGateway(num, mensaje)
         

# Initialize Firebase connection
fireb = pyrebase.initialize_app(config.firebaseConf)
db = fireb.database()

def stream_handler(message):
    print('event={m[event]}; path={m[path]}; data={m[data]}'
        .format(m=message))

    if (message["event"] == "put" and message["path"] == "/"):
      for command in message["data"]:
        print("Command JEMC1: " + command)
        data = message["data"][command]
        for key,val in data.items():
          print(key, "=>", val)
        numero=data["number"]
        comando=data["command"]
        status=data["status"]
        firebase_key = command
        
        print('comando:' + comando + 'status: ' + status)
        # if number found in db, create new record with command and status = PENDING
        # else add command to queue
        record = p.getRecordByNumber(numero)
        if (status == "ALERT"):
          sendAlert(numero, comando)
          data = {"status": "ANSWERED"}
          update_firebase(firebase_key, data)
        elif (record.count() > 0):
          print("Storing PENDING command for number: " + numero)
          msg=mensaje_class()
          msg.destination = str(numero)
          msg.contents = comando
          msg.command_id = str(uuid.uuid4())
          msg.firebase_key = command
          msg.status = "PENDING"
          p.storeCommand(msg)
        elif (status == 'INITIAL'):
          sendMessage(numero, comando, firebase_key)

    elif (message["event"] == "put" and message["data"]):
        numero=message["data"]["number"]
        comando=message["data"]["command"]
        status=message["data"]["status"]
        # Get firebase key from path, remove the "/"
        path =  message["path"]
        firebase_key = path[1:]
        print("JEMC2 firebase_key: " + firebase_key)
        if (status == "ALERT"):
          sendAlert(numero,comando)
          data = {"status": "ANSWERED"}
          update_firebase(firebase_key, data)
        else:
          print('Command JEMC2:' + comando)
          print("Status from firebase: " + status)

          sendmsg(numero, comando, firebase_key)
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
