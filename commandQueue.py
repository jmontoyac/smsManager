
import queue
import sys
import config
from time import sleep
import pymongo
import persistence as p
import threading
import uuid

# Database connection
myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["sosDatabase"]

# Borrar despues de pruebas
find = ""


command_queue = queue.Queue()

# Class to hold a message
class message:
	destination = ""
	contents = ""
	status = "INITIAL"
	retried_times = 1
	command_id = ""

	def send_sms():
		print('Sendig message')
		sleep(config.SMS_RESPONSE_TIMEOUT)
		# Send message to SMS Gateway
		# Write record to database

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

# This is the worker for threading
def send_mesage():
	while not command_queue.empty():	
	    # Get message from queue
	    msg = command_queue.get()
	    print ("Getting message from queue")
	    print ("Destination: " + msg.destination)
	    print ("Message: " + msg.contents)
	    msg.status = "SENT"
	    print ("Status: " + msg.status)
	    print ("Id: " + str(msg.command_id))
	    print ("Sending message")
	    print ("Wait for response timeout in seconds: " + str(config.SMS_RESPONSE_TIMEOUT))
	    print ("-----------------------------------------------")
	    # Store message to database
	    p.storeCommand(msg)
	    sleep(10)
	    print ("Message to " + msg.destination)
	    timer = threading.Timer(config.SMS_RESPONSE_TIMEOUT, timer_expired)
	    timer.setName(msg.command_id)
	    timer.start()

	    	#sleep(config.SMS_RESPONSE_TIMEOUT)
	print ("Sent all messages from queue, wait for responses")


def main(argv):
	print ("Add all arguments to command queue")
	print ("argv length: " + str(len(argv)))
	x=0
	while x< len(argv):
		m = message()
		m.destination = argv[x]
		m.contents = argv[x+1]
		m.command_id = str(uuid.uuid4())
		# if number foun in db, create new record wuth command and status = PENDING
		# else add command to queue
		record = p.getRecordByNumber(m.destination)
		if (record.count() > 0):
			print("Storing PENDING command for number: " + m.destination)
			m.status = "PENDING"
			p.storeCommand(m)
		else:
			command_queue.put(m)
		x+=2

	send_mesage()	

# Start with python commandQueue number1 message1 number2 message2
if __name__ == "__main__":
	main(sys.argv[1:])
