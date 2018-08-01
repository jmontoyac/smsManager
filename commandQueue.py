
import Queue
import sys
import config
from time import sleep

command_queue = Queue.Queue()

# Class to hold a message
class message:
	destination = ""
	contents = ""
	status = "INITIAL"

# This is the worker for threading
def send_mesage():
	while not command_queue.empty():	
	    # Get message from queue
	    msg = command_queue.get()
	    print "Getting message from queue"
	    print "Destination: " + msg.destination
	    print "Message: " + msg.contents
	    print "Status: " + msg.status
	    print "Sending message"
	    print "Wait for response timeout in seconds: " + str(config.SMS_RESPONSE_TIMEOUT)
	    print "-----------------------------------------------"
	    for x in range(config.SMS_RETRIES):
	    	print "Message to " + msg.destination + " attempt: " + str(x+1) + " out of " + str(config.SMS_RETRIES)
	    	sleep(config.SMS_RESPONSE_TIMEOUT)
	print "Sent all messages from queue"


def main(argv):
	print "Add all arguments to command queue"
	print "argv length: " + str(len(argv))
	x=0
	while x< len(argv):
		m = message()
		m.destination = argv[x]
		m.contents = argv[x+1]
		command_queue.put(m)
		x+=2
	sleep(3)
	send_mesage()

if __name__ == "__main__":
	main(sys.argv[1:])
