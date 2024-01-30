# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=line-too-long

# !/usr/bin/env python3

import sqlite3 as sql
import os
import logging
from logging import Logger
import config_constants as const
from terminal_colors import TerminalColors

def create_database(number_of_secret):
    if os.path.exists(const.DB_FILE_NAME):
        os.remove(const.DB_FILE_NAME)
        logging.info('%sAn old file: %s deleted successfully.%s', TerminalColors.YELLOW, const.DB_FILE_NAME, TerminalColors.RESET)
    connection = sql.connect(const.DB_FILE_NAME)
    cursor = connection.cursor()

    cursor.execute('PRAGMA foreign_keys = ON')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Main_access
            (card_id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_number TEXT UNIQUE,
            timestamp TEXT)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS Main_history
            (entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_number TEXT,
            timestamp TEXT,
            result INTEGER)''')

    for i in range(number_of_secret):
        cursor.execute(f'''CREATE TABLE IF NOT EXISTS Secret_{i+1}_access
            (card_id INTEGER PRIMARY KEY,
            pin TEXT,
            timestamp TEXT,
            CONSTRAINT s1a_fk
            FOREIGN KEY(card_id) REFERENCES Main_access(card_id))''')

        cursor.execute(f'''CREATE TABLE IF NOT EXISTS Secret_{i+1}_history
                (entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_number TEXT,
                timestamp TEXT,
                result INTEGER)''')

    connection.commit()
    connection.close()
    logging.info('%sNew database: %s created successfully.%s', TerminalColors.YELLOW, const.DB_FILE_NAME, TerminalColors.RESET)

def add_card_main_access(card_number, timestamp, logger: Logger):
    connection = sql.connect(const.DB_FILE_NAME)
    cursor = connection.cursor()
    cursor.execute('SELECT card_id FROM Main_access WHERE card_number = ?', (card_number,))
    res = cursor.fetchone()
    if not res:
        cursor.execute('INSERT INTO Main_access (card_number, timestamp) VALUES (?,?)', (card_number, timestamp,))
        connection.commit()
        logger.info('%s[Main_access]%s Registered card with number: %s, at time: %s as a trusted one.%s',
                     TerminalColors.BLUE, TerminalColors.YELLOW, card_number, timestamp, TerminalColors.RESET)
    else:
        logger.info('%s[Main_access]%s Card with number: %s already exists.%s',
                     TerminalColors.BLUE, TerminalColors.YELLOW, card_number, TerminalColors.RESET)
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
    return result == 1

def add_card_secret_access(secret_id, card_number, pin, timestamp):
    connection = sql.connect(const.DB_FILE_NAME)
    cursor = connection.cursor()
    cursor.execute('SELECT card_id FROM Main_access WHERE card_number = ?', (card_number,))
    res = cursor.fetchone()
    if not res:
        cursor.execute('INSERT INTO Main_access (card_number, timestamp) VALUES (?,?)', (card_number, timestamp,))
        cursor.execute('SELECT card_id FROM Main_access WHERE card_number = ?', (card_number,))
        res = cursor.fetchone()
    if res:
        cursor.execute(f'SELECT card_id FROM Secret_{secret_id}_access WHERE card_id = ?', (res[0],))
        res_2 = cursor.fetchone()
        if not res_2:
            cursor.execute(f'INSERT INTO Secret_{secret_id}_access (card_id, pin, timestamp) VALUES (?,?,?)', (res[0], pin, timestamp,))
            connection.commit()
    connection.close()

def check_register_card_secret_access(secret_id, card_number, pin, timestamp):
    connection = sql.connect(const.DB_FILE_NAME)
    cursor = connection.cursor()
    cursor.execute('SELECT card_id FROM Main_access WHERE card_number = ?', (card_number,))
    res = cursor.fetchone()
    result = 0
    if res:
        cursor.execute(f'SELECT pin FROM Secret_{secret_id}_access WHERE card_id = ?', (res[0],))
        res = cursor.fetchone()
        if res and res[0]==pin:
            result = 1

    cursor.execute(f'INSERT INTO Secret_{secret_id}_history (card_number, timestamp, result) VALUES (?,?,?)', (card_number, timestamp, result))
    connection.commit()
    connection.close()
    return result == 1

def get_n_entries_from_table(table_name: str, n):
    connection = sql.connect(const.DB_FILE_NAME)
    cursor = connection.cursor()
    # Ensure the table name is sanitized to prevent SQL injection
    if not table_name.isidentifier():
        raise ValueError("Invalid table name")

    # Execute the SELECT query to retrieve n entries from the specified table
    if table_name.endswith('_history'):
        cursor.execute(f'''SELECT card_number, timestamp, result FROM {table_name} ORDER BY timestamp DESC LIMIT {n}''')
    elif table_name.startswith('Secret'):
        cursor.execute(f'''SELECT card_number, pin, S.timestamp FROM {table_name} S NATURAL JOIN Main_access M ORDER BY S.timestamp DESC LIMIT {n}''')
    else:
        cursor.execute(f'''SELECT card_number, timestamp FROM {table_name} ORDER BY timestamp DESC LIMIT {n}''')
    # Fetch the results
    entries = cursor.fetchall()
    connection.close()
    return entries

# def register_card_presence_main(card_number):
#     connection = sql.connect(const.DB_FILE_NAME)
#     cursor = connection.cursor()
#     current_timestamp = datetime.now()
#     iso_formatted_timestamp = current_timestamp.strftime(const.ISO8601)
#     result = 0
#     cursor.execute('SELECT card_id FROM Main_access WHERE card_number = ?', (card_number,))
#     res = cursor.fetchone()
#     if res:
#         result = 1
#     cursor.execute('INSERT INTO Main_history (card_number, timestamp, result) VALUES (?,?,?)', (card_number, iso_formatted_timestamp, result))
#     connection.commit()
#     connection.close()

# def register_card_presence_secret_1(card_number):
#     connection = sql.connect(const.DB_FILE_NAME)
#     cursor = connection.cursor()
#     current_timestamp = datetime.now()
#     iso_formatted_timestamp = current_timestamp.strftime(const.ISO8601)
#     result = 0
#     cursor.execute('SELECT card_id FROM Main_access WHERE card_number = ?', (card_number,))
#     res = cursor.fetchone()
#     if res:
#         cursor.execute('SELECT card_id FROM Secret_1_access WHERE card_id = ?', (res[0],))
#         res = cursor.fetchone()
#         if res:
#             result = 1
#     cursor.execute('INSERT INTO Secret_1_history (card_number, timestamp, result) VALUES (?,?,?)', (card_number, iso_formatted_timestamp, result))
#     connection.commit()
#     connection.close()

# def fill_example_data():
#     connection = sql.connect(const.DB_FILE_NAME)
#     cursor = connection.cursor()

#     for _ in range(40):
#         random_number = random.randint(10000000, 99999999)
#         add_card_main_access(random_number)

#     for _ in range(30):
#         random_number = random.randint(10000000, 99999999)
#         random_pin = random.randint(0,99)
#         add_card_secret_1_access(random_number, random_pin)

#     for _ in range(10):
#         random_number = random.randint(10000000, 99999999)
#         register_card_presence_main(random_number)

#     cursor.execute('SELECT card_number FROM Main_access')
#     entries = cursor.fetchall()
#     for ind, ent in enumerate(entries):
#         if (ind < 100):
#             card_num = ent[0]
#             for _ in range(3):
#                 register_card_presence_main(card_num)

#     cursor.execute('SELECT card_number FROM Main_access Ma JOIN Secret_1_access S1a ON Ma.card_id = S1a.card_id')
#     entries = cursor.fetchall()
#     for ind, ent in enumerate(entries):
#         if (ind < 20):
#             card_num = ent[0]
#             for _ in range(3):
#                 register_card_presence_secret_1(card_num)

#     for _ in range(20):
#         random_number = random.randint(10000000, 99999999)
#         register_card_presence_secret_1(random_number)

#     connection.commit()
#     connection.close()

# def print_data():
#     connection = sql.connect(const.DB_FILE_NAME)
#     cursor = connection.cursor()

#     cursor.execute('SELECT * FROM Main_access')
#     data = cursor.fetchall()

#     print('MAIN ACCESS data:\n')
#     for entry in data:
#         print(entry)

#     cursor.execute('SELECT * FROM Secret_1_access')
#     data = cursor.fetchall()

#     print('\n\nSECRET 1 ACCESS data:\n')
#     for entry in data:
#         print(entry)

#     cursor.execute('SELECT * FROM Main_history')
#     data = cursor.fetchall()

#     print('\n\nMAIN HISTORY data:\n')
#     for entry in data:
#         print(entry)

#     cursor.execute('SELECT * FROM Secret_1_history')
#     data = cursor.fetchall()

#     print('\n\nSECRET 1 HISTORY data:\n')
#     for entry in data:
#         print(entry)

#     connection.close()

if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s:\t%(message)s', level=logging.INFO)
    create_database(const.NUMBER_OF_SECRETS)
    # fill_example_data()
    # print_data()
