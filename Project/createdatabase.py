# #!/usr/bin/env python3

import sqlite3 as sql
import os
import config_constants as const
import logging
from terminal_colors import TerminalColors
from datetime import datetime

def create_database():
    if os.path.exists(const.DB_FILE_NAME):
        os.remove(const.DB_FILE_NAME)
        logging.info(f"{TerminalColors.YELLOW}An old file: {const.DB_FILE_NAME} deleted successfully.{TerminalColors.RESET}")
    connection = sql.connect(const.DB_FILE_NAME)
    cursor = connection.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS Office_access
            (ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Card_number text,
            Registered text)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS Secret_room_access
            (ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Card_id INTEGER,
            PIN INTEGER,
            Registered text,
            CONSTRAINT fk_id
            FOREIGN KEY (Card_id)
            REFERENCES Office_access(ID))''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS Secret_room_entry_history
            (ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Card_id INTEGER,
            Timestamp text,
            Result text,
            CONSTRAINT fk_id
            FOREIGN KEY (Card_id)
            REFERENCES Secret_room_access(ID))''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS Office_entry_history
            (ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Card_id INTEGER,
            Timestamp text,
            Result text,
            CONSTRAINT fk_id
            FOREIGN KEY (Card_id)
            REFERENCES Office_access(ID))''')

    connection.commit()
    connection.close()
    logging.info(f"{TerminalColors.YELLOW}New database: {const.DB_FILE_NAME} created successfully.{TerminalColors.RESET}")

def fill_example_data():
    connection = sql.connect(const.DB_FILE_NAME)
    cursor = connection.cursor()
    cursor.execute('PRAGMA foreign_keys = ON')
    current_timestamp = datetime.now()
    iso_formatted_timestamp = current_timestamp.strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('INSERT INTO Office_access (Card_number, Registered) VALUES (?,?)', ('000266545',iso_formatted_timestamp,))
    cursor.execute('INSERT INTO Office_access (Card_number, Registered) VALUES (?,?)', ('000264711',iso_formatted_timestamp,))
    card_1_id = cursor.execute('SELECT ID FROM Office_access WHERE Card_number = ?', ('000266545',)).fetchone()[0]
    card_2_id = cursor.execute('SELECT ID FROM Office_access WHERE Card_number = ?', ('000264711',)).fetchone()[0]
    cursor.execute('INSERT INTO Secret_room_access (Card_id, PIN, Registered) VALUES (?,?,?)', (card_1_id,7,iso_formatted_timestamp,))
    cursor.execute('INSERT INTO Secret_room_access (Card_id, PIN, Registered) VALUES (?,?,?)', (card_2_id,10,iso_formatted_timestamp,))
    # cursor.execute('INSERT INTO Secret_room_access (Card_id, PIN) VALUES (?,?)', ('000264711',10,))
    # cursor.execute('INSERT INTO Secret_room_access (ID,Card_id, PIN) VALUES (,?,?)', ('000266545'))
    # cursor.execute('INSERT INTO Secret_room_access (ID, Card_id, PIN) VALUES (,?,?)', ('000264711'))
    connection.commit()
    connection.close()

def print_data():
    connection = sql.connect(const.DB_FILE_NAME)
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM Office_access')
    office_access_data = cursor.fetchall()

    for entry in office_access_data:
        print(entry)
    
    cursor.execute('SELECT * FROM Secret_room_access')
    secret_access_data = cursor.fetchall()

    for entry in secret_access_data:
        print(entry)


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s:\t%(message)s', level=logging.INFO)
    create_database()
    fill_example_data()
    print_data()
