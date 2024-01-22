ACCEPT_ACCESS_COOLDOWN = 5000 #time in millis
BUTTON_PRESSED_COOLDOWN = 1500
DB_FILE_NAME = 'rfid_server.db'

SERVER_BROKER = '10.33.108.127'
OFFICE_ENTRANCE_BROKER = '10.33.108.127'
SECRET_ROOM_BROKER = '10.33.108.127'

MAIN_TOPIC_ADD = 'main/add' # publisher: rfid, subscriber: server
MAIN_TOPIC_CHECK_REQUEST = 'main/check/request' # publisher: rfid, subscriber: server
MAIN_TOPIC_CHECK_RESPONSE = 'main/check/response' # publisher: server, subscriber: rfid

SECRET_TOPIC_ADD = 'secret/add' # publisher: rfid, subscriber: server
SECRET_TOPIC_CHECK_REQUEST = 'secret/check/request' # publisher: rfid, subscriber: server
SECRET_TOPIC_CHECK_RESPONSE = 'secret/check/response' # publisher: server, subscriber: rfid

TOKEN_CHECK_REQUEST = 'token/check/request' # publisher: rfid, subscriber: server
TOKEN_CHECK_RESPONSE = 'token/check/response' # publisher: server, subscriber: rfid

ACCEPT_MESSAGE = 'Accepted'
DENY_MESSAGE = 'Denied'

ISO8601 = '%Y-%m-%d %H:%M:%S'

GENERATE_TOKEN_PERIOD = 20 #time in SECONDS
TOKEN_CHANGE_COOLDOWN = 5 #time in SECONDS