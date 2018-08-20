import config
from quiubas import Quiubas

quiubas = Quiubas()
quiubas.setAuth( config.api_key, config.api_private )

response = quiubas.sms.send( {
	'to_number': '+528442462790',
	'message' : 'Hello there'
})

print response


