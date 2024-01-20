import argparse
import threading
import time
import datetime
import random
import config_constants as const

parser = argparse.ArgumentParser(description='Program for the RFiD card presence system administrator')
token = None
prev_token = None
token_change_timestamp = time.time()-const.GENERATE_TOKEN_PERIOD
exit_event = threading.Event()

def update_token():
    global token, prev_token, token_change_timestamp
    prev_token = token
    token = random.randint(0,99)
    token_change_timestamp = time.time()

def generate_tokens():
    while not exit_event.is_set():
        time_now = time.time()
        if (time_now - token_change_timestamp >= const.GENERATE_TOKEN_PERIOD):
            update_token()

def check_token(number_to_check):
    current_timestamp = time.time()

    if current_timestamp - token_change_timestamp < const.TOKEN_CHANGE_COOLDOWN:
        return number_to_check == token or number_to_check == prev_token
    else:
        return number_to_check == token

def config_parser():
    global parser
    parser.add_argument('-r', '--reader', help='Specify the card reader')
    parser.add_argument('-tc', '--token-check', default=None, help='Check if provided token is correct')
    parser.add_argument('-lh', '--list-history', action='store_true', help='Print card presence history from the specified reader')
    parser.add_argument('-t', '--token', action='store_true', help='Print the current token')
    parser.add_argument('--exit', action='store_true', help='Terminate this program')

def program():
    config_parser()

    program_exit_flag = False

    # token_thread = threading.Thread(target=generate_tokens)
    # token_thread.start()

    while not program_exit_flag:
        arguments = input('Command: ')
        args, unknown = parser.parse_known_args(arguments.split())
        if args.list_history:
            print('History print required!')
        elif args.token:
            token_change_datetime = datetime.datetime.fromtimestamp(token_change_timestamp).strftime('%c')
            print(f'Token [{token_change_datetime}]:\t{token}')
        elif (args.token_check is not None):
            print(args.token_check)
            print(f'Token check:\t{check_token(int(args.token_check))}')
        elif args.exit:
            print('Terminating the program...')
            program_exit_flag = True
            # exit_event.set()
            # token_thread.join()
        else:
            print(f'Unknown commands: {unknown}')

if __name__ == '__main__':
    token_thread = threading.Thread(target=generate_tokens)
    token_thread.start()
    program()
    exit_event.set()
    token_thread.join()
    print('----------------------------------')
    print('FINISHED')