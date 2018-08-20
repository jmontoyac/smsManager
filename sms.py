from flask import Flask, request
from twilio.twiml.messaging_response import Message, MessagingResponse 
from pyrebase import pyrebase
import config
import pymongo
import persistence as p
import logger

app = Flask(__name__)
log = logger.logging.getLogger('sos.sms')
 
def saveResponse(num,resp):
    print('saveResponse({},{})'.format(num,resp))
    com = db.child("Commands").order_by_child("number").equal_to(num).order_by_child("status").equal_to("INITIAL").limit_to_last(5).get()
    print('Command: '+ str(com.val()))
    log.debug('Command: ' + str(com.val()))
    list = com.val()
    print('List ' + str(list.keys()))
    key=[*list.keys()]
    for k in key:
        data=list[k]
        if (data["status"] == "INITIAL" and data["number"] == num ):
          print('Number ' + num)
          log.debug('Number: ' + num)
          #data=list[key[0]]
          data['response']=resp
          data['status']='ANSWERED'
          print('Data ' +str(data))
          log.debug('Data: ' + str(data))
          # Update smsManager database with status ANSWERED for this message
          sent = p.getSentByNumber(data["number"])
          if (sent.count() > 0):
              for x in sent:
                  commandId = x["command_id"]
              p.updateStatus(commandId,"ANSWERED")
              db.child("Commands").child(k).update(data)

@app.route('/sms', methods=['POST'])
def sms():
    number = request.form['From']
    message_body = request.form['Body']
    print('mensaje: '+message_body) 
    log.debug('Mensaje: ' + message_body)
    resp = MessagingResponse()
    print("Respuesta: " + str(resp))
    #log('Respuesta: ' + str(resp))
    #resp.message('Hello {}, you said: {}'.format(number, message_body))
    saveResponse(number,message_body)
    return str(resp)
@app.route('/sms',methods=['GET'])
def test():
    print('get en sms') 

fireb = pyrebase.initialize_app(config.firebaseConf)
db = fireb.database()

if __name__ == '__main__':
    app.run(host='0.0.0.0')
