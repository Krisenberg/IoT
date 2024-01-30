
#!/usr/bin/env python3

import time
import threading
import datetime
import logging
import argparse
import random
from http.server import HTTPServer, SimpleHTTPRequestHandler
import config_constants as const
from terminal_colors import TerminalColors
import database as db

class TokenData():
    def __init__(self):
        self.token = -1
        self.prev_token = -1
        self.token_change_timestamp = time.time()-const.GENERATE_TOKEN_PERIOD

    def check_token(self, token_str):
        current_timestamp = time.time()
        if current_timestamp - self.token_change_timestamp < const.TOKEN_CHANGE_COOLDOWN:
            return token_str == str(self.token) or token_str == str(self.prev_token)
        return token_str == str(self.token)

    def update_token(self):
        self.prev_token = self.token
        self.token = random.randint(0,77)
        self.token_change_timestamp = time.time()
        timestamp_iso = datetime.datetime.fromtimestamp(self.token_change_timestamp).strftime(const.ISO8601)
        LOGGER.info('%sGenerated new token at %s:%s %s  --->  %s%s', TerminalColors.YELLOW, timestamp_iso, TerminalColors.RED, self.prev_token, self.token, TerminalColors.RESET)

class CustomHandler(SimpleHTTPRequestHandler):
    def setup(self):
        SimpleHTTPRequestHandler.setup(self)
        self.request.settimeout(30)
    def do_GET(self):
        if self.path.endswith(".css"):
            self.send_response(200)
            self.send_header("Content-type", "text/css")
            self.end_headers()
            with open('Project/website/styles.css', 'rb') as file:
                content = file.read()
                self.wfile.write(content)
        # Specify the custom path for your index.html file
        elif self.path == '/':
            # Your custom logic to serve the index.html file
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            # Open and read the content of your index.html file
            with open('Project/website/index.html', 'rb') as file:
                content = file.read()
                current_token = str(TOKEN_DATA.token)
                timestamp = time.time()
                time_to_token_change = (int) (TOKEN_DATA.token_change_timestamp + const.GENERATE_TOKEN_PERIOD - timestamp - 3) # minus 3 because of the website reload time
                js_time_to_change_set = f'var timeleft = {time_to_token_change};'
                js_time_to_change_set_bytes = js_time_to_change_set.encode('utf-8')
                js_code = f'$(document).ready(function() {{ $("#token").text({current_token}); }});'
                js_code_bytes = js_code.encode('utf-8')

                # Replace a bytes-like object in content with another bytes-like object
                content = content.replace(b'var timeleft = 0;', js_time_to_change_set_bytes + js_code_bytes)

            # Send the content as the response
            self.wfile.write(content)
        else:
            # If the path doesn't match, fall back to the default behavior
            super().do_GET()
    def log_message(self, format, *args):
        LOGGER.debug('%s%s%s - - [%s] %s', TerminalColors.YELLOW, self.address_string(), TerminalColors.RESET, self.log_date_time_string(), format%args)

PARSER = argparse.ArgumentParser(description='Program for the RFiD card presence system administrator', add_help=False)
TOKEN_DATA = TokenData()
EXIT_EVENT = threading.Event()
LOGGER = logging.getLogger(__name__)

SERVER_ADDRESS = ('', 8765)
HTTPD = HTTPServer(SERVER_ADDRESS, CustomHandler)

def add_card_to_trusted(message):
    message_decoded = message.split("&")
    if len(message_decoded) == 2:
        num = message_decoded[0]
        timestamp = message_decoded[1]
        db.add_card_main_access(num, timestamp, LOGGER)
    elif len(message_decoded) == 4:
        client_id = message_decoded[0]
        num = message_decoded[1]
        pin = message_decoded[2]
        timestamp = message_decoded[3]
        db.add_card_secret_access(client_id, num, pin, timestamp)

def check_card_request(message):
    message_decoded = message.split("&")
    if len(message_decoded) == 2:
        num = message_decoded[0]
        timestamp = message_decoded[1]
        check = db.check_register_card_main_access(num, timestamp)
        if check:
            print(f'{const.MAIN_TOPIC_CHECK_RESPONSE} ---> {const.ACCEPT_MESSAGE}')
        else:
            print(f'{const.MAIN_TOPIC_CHECK_RESPONSE} ---> {const.DENY_MESSAGE}')
    elif len(message_decoded) == 4:
        client_id = message_decoded[0]
        num = message_decoded[1]
        pin = message_decoded[2]
        timestamp = message_decoded[3]
        check = db.check_register_card_secret_access(client_id, num, pin, timestamp)
        client_to_publish = mqtt_clients[int(client_id)]
        if check:
            print(f'{const.SECRET_TOPIC_CHECK_RESPONSE} ---> {const.ACCEPT_MESSAGE}')
        else:
            print(f'{const.SECRET_TOPIC_CHECK_RESPONSE} ---> {const.DENY_MESSAGE}')

def check_rfid_token(message):
    message_decoded = message.split("&")
    if len(message_decoded) == 1:
        token = message_decoded[0]
        check = check_token(token)
        if check:
            print(f'{const.MAIN_TOKEN_CHECK_RESPONSE} ---> {const.ACCEPT_MESSAGE}')
        else:
            print(f'{const.MAIN_TOKEN_CHECK_RESPONSE} ---> {const.DENY_MESSAGE}')
    elif len(message_decoded) == 2:
        client_id = message_decoded[0]
        token = message_decoded[1]
        check = check_token(token)
        client_to_publish = mqtt_clients[int(client_id)]
        if check:
            print(f'{const.SECRET_TOKEN_CHECK_RESPONSE} ---> {const.ACCEPT_MESSAGE}')
        else:
            print(f'{const.SECRET_TOKEN_CHECK_RESPONSE} ---> {const.DENY_MESSAGE}')

# def add_card_to_trusted_secret(_client, _userdata, message,):
#     message_decoded = (str(message.payload.decode("utf-8"))).split("&")
#     if len(message_decoded) == 4:
#         sercet_id = message_decoded[0]
#         num = message_decoded[1]
#         pin = message_decoded[2]
#         timestamp = message_decoded[3]
#         db.add_card_secret_access(sercet_id, num, pin, timestamp)
#         logging.info('%s[Secret_1_access]%s Registered card with number: %s and %s at time: %s as a trusted one.%s',
#                      TerminalColors.BLUE, TerminalColors.YELLOW, num, pin, timestamp, TerminalColors.RESET)

# def check_card_request_secret(_client, _userdata, message,):
#     message_decoded = (str(message.payload.decode("utf-8"))).split("&")
#     if len(message_decoded) == 3:
#         sercet_id = message_decoded[0]
#         num = message_decoded[1]
#         pin = message_decoded[2]
#         timestamp = message_decoded[3]
#         check = db.check_register_card_secret_access(sercet_id, num, pin, timestamp)
#         if check:
#             client_secret_1.publish(const.SECRET_TOPIC_CHECK_RESPONSE, const.ACCEPT_MESSAGE)
#         else:
#             client_secret_1.publish(const.SECRET_TOPIC_CHECK_RESPONSE, const.DENY_MESSAGE)

# def check_rfid_token_secret(_client, _userdata, message,):
#     message_decoded = (str(message.payload.decode("utf-8")))
#     if len(message_decoded) == 2:
#         _ = message_decoded[0]
#         token = message_decoded[1]
#         check = check_token(token)
#         if check:
#             client_secret_1.publish(const.SECRET_TOKEN_CHECK_RESPONSE, const.ACCEPT_MESSAGE)
#         else:
#             client_secret_1.publish(const.SECRET_TOKEN_CHECK_RESPONSE, const.DENY_MESSAGE)

mqtt_clients = {
    0 : 'client_main',
    1 : 'client_secret_1'
}

def generate_tokens():
    while not EXIT_EVENT.is_set():
        time_now = time.time()
        if time_now - TOKEN_DATA.token_change_timestamp >= const.GENERATE_TOKEN_PERIOD:
            TOKEN_DATA.update_token()

def check_token(token_str):
    return TOKEN_DATA.check_token(token_str)

def config_parser():
    PARSER.add_argument('-r', '--reader', help='Specify the card reader')
    PARSER.add_argument('-lh', '--list-history', action='store_true', help='Print card presence history from the specified reader')
    PARSER.add_argument('-t', '--token', action='store_true', help='Print the current token')
    PARSER.add_argument('--exit', action='store_true', help='Terminate this program')
    PARSER.add_argument('-d', '--debug', action="store_true", help="Set the logging level to DEBUG")
    PARSER.add_argument('-i', '--info', action="store_true", help="Set the logging level to INFO")
    PARSER.add_argument('-w', '--warning', action="store_true", help="Set the logging level to WARNING")
    PARSER.add_argument('-e', '--error', action="store_true", help="Set the logging level to ERROR")
    PARSER.add_argument('-c', '--critical', action="store_true", help="Set the logging level to CRITICAL")
    PARSER.add_argument('-h', '--help', action='store_true', help='Display help message')
    PARSER.add_argument('-actt', action='store_true', help='Add card to trusted')
    PARSER.add_argument('-ccr', action='store_true', help='Check card request')
    PARSER.add_argument('-crt', action='store_true', help='Check token')

def list_table_entries():
    LOGGER.disabled = True
    print("\n\nTABLES")
    print('-----------------------------------------------------------------')
    index_to_table_name = {
        1 : 'Main_access',
        2 : 'Main_history'
    }
    index = 3
    for number in mqtt_clients:
        if not number == 0:
            index_to_table_name[index] = f'Secret_{number}_access'
            index += 1
            index_to_table_name[index] = f'Secret_{number}_history'
            index += 1

    for i, table in index_to_table_name.items():
        print("{:<10}{:<30}".format(f'[{i}]', table))

    flag = True
    while flag:
        user_input = input("\nSELECTION: ")
        how_many = input("HOW MANY ROWS (descending order by timestamp): ")

        # Check if both inputs are numbers
        if user_input.isdigit() and how_many.isdigit():
            # Convert the inputs to integers and break out of the loop
            user_input = int(user_input)
            how_many = int(how_many)
            flag = False
        else:
            print("Please enter valid numbers.")
    entries = db.get_n_entries_from_table(table_name=index_to_table_name[user_input], n=how_many)
    print('\nENTRIES')
    print('-----------------------------------------------------------------')
    if index_to_table_name[user_input].endswith('_history'):
        print("{:<10}{:<10}{:<30}{:<10}".format('', 'CARD', 'TIMESTAMP', 'RESULT'))
        print('-----------------------------------------------------------------')
        for i, entry in enumerate(entries):
            print("{:<10}{:<10}{:<30}{:<10}".format(f'[{i + 1}]', entry[0], entry[1], entry[2]))
    elif index_to_table_name[user_input].startswith('Secret'):
        print("{:<10}{:<10}{:<10}{:<30}".format('', 'CARD', 'PIN', 'TIMESTAMP'))
        print('-----------------------------------------------------------------')
        for i, entry in enumerate(entries):
            print("{:<10}{:<10}{:<10}{:<30}".format(f'[{i + 1}]', entry[0], entry[1], entry[2]))
    else:
        print("{:<10}{:<10}{:<30}".format('', 'CARD', 'TIMESTAMP'))
        print('-----------------------------------------------------------------')
        for i, entry in enumerate(entries):
            print("{:<10}{:<10}{:<30}".format(f'[{i + 1}]', entry[0], entry[1]))

    input("\nPress ENTER to exit the list...")
    LOGGER.disabled = False

def provide_message():
    while True:
        client_id = input("\nClient id: ")
        if client_id.isdigit():
            num = input("Number: ")
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            if int(client_id) == 0:
                return (f'{num}&{timestamp}')
            pin = input("Pin: ")
            return (f'{client_id}&{num}&{pin}&{timestamp}')

def provide_message_token():
    while True:
        client_id = input("\nClient id: ")
        if client_id.isdigit():
            token = input("Token: ")
            if int(client_id) == 0:
                return (token)
            return (f'{client_id}&{token}')

def custom_help():
    print("\n\n")
    print("{:<10}{:<30}{}".format("-r", "--reader", "Specify the card reader"))
    print("{:<10}{:<30}{}".format("-lh", "--list-history", "Print card presence history from the specified reader"))
    print("{:<10}{:<30}{}".format("-t", "--token", "Print the current token"))
    print("{:<10}{:<30}{}".format("", "--exit", "Terminate this program"))
    print("{:<10}{:<30}{}".format("-d", "--debug", "Set the logging level to DEBUG"))
    print("{:<10}{:<30}{}".format("-i", "--info", "Set the logging level to INFO"))
    print("{:<10}{:<30}{}".format("-w", "--warning", "Set the logging level to WARNING"))
    print("{:<10}{:<30}{}".format("-e", "--error", "Set the logging level to ERROR"))
    print("{:<10}{:<30}{}".format("-c", "--critical", "Set the logging level to CRITICAL"))
    print("\n\n")

def run_threaded_web_server():
    while not EXIT_EVENT.is_set():
        HTTPD.handle_request()

def run_admin_cli():
    while not EXIT_EVENT.is_set():
        arguments = input('')
        args, unknown = PARSER.parse_known_args(arguments.split())
        if args.list_history:
            list_table_entries()
        elif args.token:
            token_change_datetime = datetime.datetime.fromtimestamp(TOKEN_DATA.token_change_timestamp).strftime(const.ISO8601)
            print(f'Token [{token_change_datetime}]:\t{TOKEN_DATA.token}')
        elif args.debug:
            LOGGER.setLevel(level=logging.DEBUG)
        elif args.info:
            LOGGER.setLevel(level=logging.INFO)
        elif args.warning:
            LOGGER.setLevel(level=logging.WARNING)
        elif args.error:
            LOGGER.setLevel(level=logging.ERROR)
        elif args.critical:
            LOGGER.setLevel(level=logging.CRITICAL)
        elif args.help:
            custom_help()
        elif args.exit:
            print('Terminating the program...')
            EXIT_EVENT.set()
        elif args.actt:
            LOGGER.disabled = True
            message = provide_message()
            LOGGER.disabled = False
            add_card_to_trusted(message)
        elif args.ccr:
            LOGGER.disabled = True
            message = provide_message()
            LOGGER.disabled = False
            check_card_request(message)
        elif args.crt:
            LOGGER.disabled = True
            message = provide_message_token()
            LOGGER.disabled = False
            check_rfid_token(message)
        else:
            print(f'Unknown commands: {unknown}')

token_thread = threading.Thread(target=generate_tokens)
web_thread = threading.Thread(target=run_threaded_web_server)
input_thread = threading.Thread(target=run_admin_cli)
threads = [token_thread, web_thread, input_thread]

def run_server():
    logging.basicConfig(format='%(levelname)s:\t%(message)s', level=logging.INFO)
    config_parser()
    # connect_mqtts()

    for thr in threads:
        thr.start()

    while not EXIT_EVENT.is_set():
        continue

    for thr in threads:
        thr.join()

    # disconnect_mqtts()

if __name__ == "__main__":
    run_server()
    print('----------------------------------')
    print('FINISHED')