# smsManager
Handle the sending and reception of SMS triggered by Firebase and sent by Twilio

A FSM is implemented to handle messages to be sent to Twilio (next will be to any SMS Gateway), keeping track of answered / unanswered messages, retry the sending of unanswered messages up to configurable times.
It also stores new messages bound to the same destination and sends them only after the previous message has been answered.

The application is multi-threaded for the sending of messages and has a listening HTTP server to get the answer callbacks.
