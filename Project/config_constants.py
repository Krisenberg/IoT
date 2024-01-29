# pylint: disable=missing-module-docstring

ACCEPT_ACCESS_COOLDOWN = 5000 #time in millis
BUTTON_PRESSED_COOLDOWN = 1500
DB_FILE_NAME = 'rfid_server.db'
NUMBER_OF_SECRETS = 1

SERVER_BROKER = '10.33.108.127'
OFFICE_ENTRANCE_BROKER = '10.33.108.127'
SECRET_ROOM_BROKER = '10.33.108.127'

MAIN_TOPIC_ADD = 'main/add' # publisher: rfid, subscriber: server
MAIN_TOPIC_CHECK_REQUEST = 'main/check/request' # publisher: rfid, subscriber: server
MAIN_TOPIC_CHECK_RESPONSE = 'main/check/response' # publisher: server, subscriber: rfid
MAIN_TOKEN_CHECK_REQUEST = 'main/token/request' # publisher: rfid, subscriber: server
MAIN_TOKEN_CHECK_RESPONSE = 'main/token/response' # publisher: server, subscriber: rfid

SECRET_TOPIC_ADD = 'secret/add' # publisher: rfid, subscriber: server
SECRET_TOPIC_CHECK_REQUEST = 'secret/check/request' # publisher: rfid, subscriber: server
SECRET_TOPIC_CHECK_RESPONSE = 'secret/check/response' # publisher: server, subscriber: rfid
SECRET_TOKEN_CHECK_REQUEST = 'secret/token/request' # publisher: rfid, subscriber: server
SECRET_TOKEN_CHECK_RESPONSE = 'secret/token/response' # publisher: server, subscriber: rfid

ACCEPT_MESSAGE = 'Accepted'
DENY_MESSAGE = 'Denied'

ISO8601 = '%Y-%m-%d %H:%M:%S.%f'

GENERATE_TOKEN_PERIOD = 60 #time in SECONDS
TOKEN_CHANGE_COOLDOWN = 15 #time in SECONDS
