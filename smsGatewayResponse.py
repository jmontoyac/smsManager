import config
from quiubas import Quiubas

quiubas = Quiubas()
quiubas.setAuth( config.api_key, config.api_private )

response = quiubas.sms.getResponses('72662250')

print response

