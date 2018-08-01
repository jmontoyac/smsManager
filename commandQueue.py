
import Queue
import sys
import config
from time import sleep

command_queue = Queue.Queue()

# This is the worker for threading
def send_mesage():
	while not command_queue.empty():	
	    # Get message from queue
	    print "Getting message from queue: " + str(command_queue.get())
	    print "Sending message"
	    print "Timeout seconds: " + str(config.SMS_RESPONSE_TIMEOUT)
	    sleep(config.SMS_RESPONSE_TIMEOUT)
	print "Sent all messages from queue"


def main(argv):
	print "Add all arguments to command queue"
	for arg in argv:
		command_queue.put(arg)
		print "Argument added to queue: " + str(arg)
	sleep(3)
	send_mesage()



if __name__ == "__main__":
	main(sys.argv[1:])