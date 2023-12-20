import time
import sqlite3 as sql
import datetime
import threading
import os
import logging
from test_buzzer import beep, beepSequence
from test_leds import ledsAccept, ledsDeny
from terminal_colors import TerminalColors

ACCEPT_ACCESS_COOLDOWN = 10000 #time in millis
DB_FILE_NAME = 'rfid_access_list.db'

def prepareAccessList():
    connection = sql.connect(DB_FILE_NAME)
    cursor = connection.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS Access
              (CardID INTEGER PRIMARY KEY,
              Timestamp INTEGER)''')
    cards = []

    cardsNumSet = set()

    flag = True

    timestampSeconds = time.time()
    timeString = datetime.datetime.fromtimestamp(timestampSeconds).strftime('%H:%M:%S')
    threadName = threading.current_thread().name

    while (flag):
        userInput = input(f'{TerminalColors.BLUE}[{threadName}, {timeString}]  Number: {TerminalColors.RESET}')
        if (userInput == ""):
            flag = False
        else:
            num = int(userInput)
            if num not in cardsNumSet:
                cardsNumSet.add(num)
                timestamp = int(time.time() * 1000)
                cards.append((num, timestamp))
                logging.info(f'{TerminalColors.YELLOW}Card number {num} has been added to the database.{TerminalColors.RESET}')
                beepSequence(0.5, 0.0, 1)
                time.sleep(0.5)

    cursor.executemany('INSERT INTO Access (CardID, Timestamp) VALUES (?,?)', cards)
    connection.commit()
    connection.close()

def acceptAccess(num, timestamp):
    timestampSeconds = timestamp / 1000
    timeString = datetime.datetime.fromtimestamp(timestampSeconds).strftime('%H:%M:%S')
    threadName = threading.current_thread().name
    print(f'{TerminalColors.GREEN}[{threadName}]  Accepted card with number: {num}, at time: {timeString}{TerminalColors.RESET}')
    ledsAccept(1)
    beepSequence(0.25, 0.25, 3)
    
def denyAccess(num, timestamp):
    timestampSeconds = timestamp / 1000
    timeString = datetime.datetime.fromtimestamp(timestampSeconds).strftime('%H:%M:%S')
    threadName = threading.current_thread().name
    print(f'{TerminalColors.RED}[{threadName}]  Denied card with number: {num}, at time: {timeString}{TerminalColors.RESET}')
    ledsDeny(1)


def rfidRead():

    connection = sql.connect(DB_FILE_NAME)
    cursor = connection.cursor()

    flag = True

    timestampSeconds = time.time()
    timeString = datetime.datetime.fromtimestamp(timestampSeconds).strftime('%H:%M:%S')
    threadName = threading.current_thread().name

    while (flag):
        userInput = input(f"{TerminalColors.BLUE}[{threadName}, {timeString}]  Number: {TerminalColors.RESET}")
        if (userInput == ""):
            flag = False
        else:
            num = int(userInput)
            timestamp = int(time.time() * 1000)
            cursor.execute('SELECT * FROM Access WHERE CardID = ?', (num,))
            entry = cursor.fetchone()
            if (entry and timestamp >= entry[1] + ACCEPT_ACCESS_COOLDOWN):
                cursor.execute('UPDATE Access SET Timestamp = ? WHERE CardID = ?', (timestamp, num))
                connection.commit()
                acceptAccess(num, timestamp)
            else:
                denyAccess(num, timestamp)
    connection.close()

def delete_db_file():
    try:
        os.remove(DB_FILE_NAME)
        logging.info(f"{TerminalColors.YELLOW}{DB_FILE_NAME} deleted successfully.{TerminalColors.RESET}")
    except FileNotFoundError:
        logging.info(f"{TerminalColors.RED}{DB_FILE_NAME} does not exist.{TerminalColors.RESET}")

def program():
    logging.basicConfig(format='%(levelname)s:\t%(message)s', level=logging.INFO)

    print('\nPlease configure the Database to store authorized RFIDs.')
    print('Place the cards you want to be marked as authorized' +
           'close to the reader (on the right side of the set).')
    
    prepareAccessList()

    print('The Access List has been configured successfully.')
    print('-------------------------------------------------\n\n\n')
    print('Place the card close to the reader (on the right side of the set).')

    rfidRead()

    delete_db_file()
    print('RFID reader is no more active. Program has terminated.')

if __name__ == "__main__":
    program()