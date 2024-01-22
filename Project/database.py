# !/usr/bin/env python3

import sqlite3 as sql
import os
import config_constants as const
import logging
from terminal_colors import TerminalColors
from datetime import datetime, timedelta
import random

def create_database():
    if os.path.exists(const.DB_FILE_NAME):
        os.remove(const.DB_FILE_NAME)
        logging.info(f"{TerminalColors.YELLOW}An old file: {const.DB_FILE_NAME} deleted successfully.{TerminalColors.RESET}")
    connection = sql.connect(const.DB_FILE_NAME)
    cursor = connection.cursor()
    
    cursor.execute('PRAGMA foreign_keys = ON')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Main_access
            (card_id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_number TEXT UNIQUE,
            registered TEXT)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS Secret_1_access
            (card_id INTEGER PRIMARY KEY,
            pin TEXT,
            registered TEXT,
            CONSTRAINT s1a_fk
            FOREIGN KEY(card_id) REFERENCES Main_access(card_id))''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS Secret_1_history
            (entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_number TEXT,
            timestamp TEXT,
            result INTEGER)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS Main_history
            (entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_number TEXT,
            timestamp TEXT,
            result INTEGER)''')

    connection.commit()
    connection.close()
    logging.info(f"{TerminalColors.YELLOW}New database: {const.DB_FILE_NAME} created successfully.{TerminalColors.RESET}")

def add_card_secret_1_access(card_number, pin, timestamp):
    connection = sql.connect(const.DB_FILE_NAME)
    cursor = connection.cursor()
    # current_timestamp = datetime.now()
    # iso_formatted_timestamp = current_timestamp.strftime(const.ISO8601)
    cursor.execute('SELECT card_id FROM Main_access WHERE card_number = ?', (card_number,))
    res = cursor.fetchone()
    if not res:
        cursor.execute('INSERT INTO Main_access (card_number, registered) VALUES (?,?)', (card_number, timestamp,))
        cursor.execute('SELECT card_id FROM Main_access WHERE card_number = ?', (card_number,))
        res = cursor.fetchone()
    if res:
        cursor.execute('SELECT card_id FROM Secret_1_access WHERE card_id = ?', (res[0],))
        res_2 = cursor.fetchone()
        if not res_2:
            cursor.execute('INSERT INTO Secret_1_access (card_id, pin, registered) VALUES (?,?,?)', (res[0], pin, timestamp,))
            connection.commit()
    connection.close()

def add_card_main_access(card_number, timestamp):
    connection = sql.connect(const.DB_FILE_NAME)
    cursor = connection.cursor()
    # current_timestamp = datetime.now()
    # iso_formatted_timestamp = current_timestamp.strftime(const.ISO8601)
    cursor.execute('SELECT card_id FROM Main_access WHERE card_number = ?', (card_number,))
    res = cursor.fetchone()
    if not res:
        cursor.execute('INSERT INTO Main_access (card_number, registered) VALUES (?,?)', (card_number, timestamp,))
        connection.commit()
    connection.close()

def check_register_card_main_access(card_number, timestamp):
    connection = sql.connect(const.DB_FILE_NAME)
    cursor = connection.cursor()
    cursor.execute('SELECT card_id FROM Main_access WHERE card_number = ?', (card_number,))
    res = cursor.fetchone()
    result = 1 if res else 0

    cursor.execute('INSERT INTO Main_history (card_number, timestamp, result) VALUES (?,?,?)', (card_number, timestamp, result))
    connection.commit()
    connection.close()
    if res:
        return True
    return False

def check_card_secret_1_access(card_number):
    connection = sql.connect(const.DB_FILE_NAME)
    cursor = connection.cursor()
    cursor.execute('SELECT card_id FROM Secret_1_access WHERE card_number = ?', (card_number,))
    res = cursor.fetchone()
    connection.close()
    if res:
        return True
    return False

def register_card_presence_main(card_number):
    connection = sql.connect(const.DB_FILE_NAME)
    cursor = connection.cursor()
    current_timestamp = datetime.now()
    iso_formatted_timestamp = current_timestamp.strftime(const.ISO8601)
    result = 0
    cursor.execute('SELECT card_id FROM Main_access WHERE card_number = ?', (card_number,))
    res = cursor.fetchone()
    if res:
        result = 1
    cursor.execute('INSERT INTO Main_history (card_number, timestamp, result) VALUES (?,?,?)', (card_number, iso_formatted_timestamp, result))
    connection.commit()
    connection.close()

def register_card_presence_secret_1(card_number):
    connection = sql.connect(const.DB_FILE_NAME)
    cursor = connection.cursor()
    current_timestamp = datetime.now()
    iso_formatted_timestamp = current_timestamp.strftime(const.ISO8601)
    result = 0
    cursor.execute('SELECT card_id FROM Main_access WHERE card_number = ?', (card_number,))
    res = cursor.fetchone()
    if res:
        cursor.execute('SELECT card_id FROM Secret_1_access WHERE card_id = ?', (res[0],))
        res = cursor.fetchone()
        if res:
            result = 1
    cursor.execute('INSERT INTO Secret_1_history (card_number, timestamp, result) VALUES (?,?,?)', (card_number, iso_formatted_timestamp, result))
    connection.commit()
    connection.close()    

def fill_example_data():
    connection = sql.connect(const.DB_FILE_NAME)
    cursor = connection.cursor()

    for _ in range(40):
        random_number = random.randint(10000000, 99999999)
        add_card_main_access(random_number)
    
    for _ in range(30):
        random_number = random.randint(10000000, 99999999)
        random_pin = random.randint(0,99)
        add_card_secret_1_access(random_number, random_pin)
    
    for _ in range(10):
        random_number = random.randint(10000000, 99999999)
        register_card_presence_main(random_number)
    
    cursor.execute('SELECT card_number FROM Main_access')
    entries = cursor.fetchall()
    for ind, ent in enumerate(entries):
        if (ind < 100):
            card_num = ent[0]
            for _ in range(3):
                register_card_presence_main(card_num)
    
    cursor.execute('SELECT card_number FROM Main_access Ma JOIN Secret_1_access S1a ON Ma.card_id = S1a.card_id')
    entries = cursor.fetchall()
    for ind, ent in enumerate(entries):
        if (ind < 20):
            card_num = ent[0]
            for _ in range(3):
                register_card_presence_secret_1(card_num)

    for _ in range(20):
        random_number = random.randint(10000000, 99999999)
        register_card_presence_secret_1(random_number)

    connection.commit()
    connection.close()

def print_data():
    connection = sql.connect(const.DB_FILE_NAME)
    cursor = connection.cursor()

    cursor.execute('SELECT * FROM Main_access')
    data = cursor.fetchall()

    print('MAIN ACCESS data:\n')
    for entry in data:
        print(entry)
    
    cursor.execute('SELECT * FROM Secret_1_access')
    data = cursor.fetchall()

    print('\n\nSECRET 1 ACCESS data:\n')
    for entry in data:
        print(entry)

    cursor.execute('SELECT * FROM Main_history')
    data = cursor.fetchall()

    print('\n\nMAIN HISTORY data:\n')
    for entry in data:
        print(entry)

    cursor.execute('SELECT * FROM Secret_1_history')
    data = cursor.fetchall()

    print('\n\nSECRET 1 HISTORY data:\n')
    for entry in data:
        print(entry)
    
    connection.close()


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s:\t%(message)s', level=logging.INFO)
    create_database()
    fill_example_data()
    print_data()
