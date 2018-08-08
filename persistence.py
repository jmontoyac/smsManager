import pymongo

# Database connection
myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["sosDatabase"]


# Store command to database
def storeCommand(msg):
	mycol = mydb["commands"]
	myDictionary = {"destination": msg.destination, "message": msg.contents,
					"status": msg.status, "retries": msg.retried_times,
					"command_id": msg.command_id, "firebase_key": msg.firebase_key}

	# TODO check if number is already in DB and store with status = PENDING
	insert_result = mycol.insert_one(myDictionary)
	print ("DB inserted " + msg.destination + " message: " + msg.contents + str(msg.command_id))

# List the records in database
def listCommands():
	mycol = mydb["commands"]
	for x in mycol.find():
		print(x)


# find one record based on phone number
def find_record(number):
	mycol = mydb["commands"]
	myQuery = {"destination": number}
	myDoc = mycol.find(myQuery)
	return myDoc

# delete document (record) from collection (databae)
def delete_record(id):
	mycol = mydb["commands"]
	myQuery = {"command_id": id}
	myDoc = mycol.find(myQuery)
	for x in myDoc:
		number = x["destination"]
		command = x["message"]
	mycol.delete_one(myQuery)
	print("Deleted record for: " + number + " message: " + command) 

# Update status value
def updateStatus(id, status):
	mycol = mydb["commands"]
	myQuery = {"command_id": id}
	newValue = {"$set": {"status": status}}
	mycol.update_one(myQuery, newValue)
	print("Updated " + id + " with new status: " + status)

# Get status, returns string
def getStatus(id):
	mycol = mydb["commands"]
	myQuery = {"command_id": id}
	myDoc = mycol.find(myQuery)
	for x in myDoc:
		status = x["status"]
	return status

# Get number, returns string
def getDestination(id):
	mycol = mydb["commands"]
	myQuery = {"command_id": id}
	myDoc = mycol.find(myQuery)
	for x in myDoc:
		status = x["destination"]
	return status

# Get status, returns string
def getPendingByNumber(number):
	mycol = mydb["commands"]
	myQuery = {"destination": number, "status": "PENDING"}
	myDoc = mycol.find(myQuery)
	return myDoc

# Update retries
def updateRetries(id, num_retries):
	mycol = mydb["commands"]
	myQuery = {"command_id": id}
	newValue = {"$set": {"retries": num_retries}}
	mycol.update_one(myQuery,newValue)
	print("Updated " + id + " with new retries value: " + str(num_retries))

# Get retries, returns int
def getRetries(id):
	mycol = mydb["commands"]
	myQuery = {"command_id": id}
	myDoc = mycol.find(myQuery)
	for x in myDoc:
		retries = x["retries"]
	return retries

# Get record by ID
def getRecord(id):
	mycol = mydb["commands"]
	myQuery = {"command_id": id}
	myDoc = mycol.find(myQuery)
	#for x in myDoc:
	#	print("JEMC test: ")
		#print(x)
	return myDoc

# Get record by number
def getRecordByNumber(number):
	mycol = mydb["commands"]
	myQuery = {"destination": number}
	myDoc = mycol.find(myQuery)
	return myDoc

# Get firebase key
def getfirebase_key(id):
	mycol = mydb["commands"]
	myQuery = {"command_id": id}
	myDoc = mycol.find(myQuery)
	for x in myDoc:
		fb_id = x["firebase_key"]
	return fb_id