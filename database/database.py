import sqlite3
from pathlib import Path

def create_database_if_not_exists(database_name):
    database_file = Path(database_name)

    if not database_file.is_file():
        with sqlite3.connect(database_name) as conn:
            cursor = conn.cursor()

            # Create input_message table
            cursor.execute('''
                CREATE TABLE input_message (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create output_message table
            cursor.execute('''
                CREATE TABLE output_message (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create mobile_number table
            cursor.execute('''
                CREATE TABLE mobile_number (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    number TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()
            print(f"Database '{database_name}' created successfully.")
    else:
        print(f"Database '{database_name}' already exists.")


def show_database(database_name):
    with sqlite3.connect(database_name) as conn:
        cursor = conn.cursor()

        # Fetch and print data from input_message table
        cursor.execute('SELECT * FROM input_message')
        input_messages = cursor.fetchall()
        print("Input Message Table:")
        for row in input_messages:
            print(row)

        # Fetch and print data from output_message table
        cursor.execute('SELECT * FROM output_message')
        output_messages = cursor.fetchall()
        print("\nOutput Message Table:")
        for row in output_messages:
            print(row)

        # Fetch and print data from mobile_number table
        cursor.execute('SELECT * FROM mobile_number')
        mobile_numbers = cursor.fetchall()
        print("\nMobile Number Table:")
        for row in mobile_numbers:
            print(row)

# Example usage:
show_database('database.db')

# Example usage:
# create_database_if_not_exists('database.db')
