# pip3 install setproctitle
# pip3 install prompt-toolkit
# pip3 install PyInquirer

import sqlite3
from sqlite3 import Error
from datetime import datetime
import sys
from typing import List, Union
from PyInquirer import prompt, Validator, ValidationError
import re
from rich.table import Table
from rich.console import Console
from rich import print as print_rich
import csv

DB_DEFAULT_PATH="contacts-meetings.db"

def datetime_to_string(dt:datetime) -> str:
    return dt.strftime('%Y-%m-%d')

class Contact:
    def __init__(self, id, name, surname, birthdate, note, deleted = False):
        self.id = id
        self.name = name
        self.surname = surname        
        self.birthdate = birthdate
        """ text in format YYYY-MM-DD"""
        self.note = note
        self.deleted = deleted

    def _str_(self) -> str:
        return f'{self.name} {self.surname} {self.birthdate} {self.note}'

    def __repr__(self) -> str:
        return self._str_()


class Connection:
    def __init__(self, id, id_contact, phone_privat, phone_work, phone_secret, email_privat, email_work, email_secret, whatsup, telegram, signal, hangouts, deleted = False):
        self.id = id
        self.id_contact = id_contact
        self.phone_privat = phone_privat
        self.phone_work = phone_work
        self.phone_secret = phone_secret
        self.email_privat = email_privat
        self.email_work = email_work
        self.email_secret = email_secret
        self.whatsup = whatsup
        self.telegram = telegram
        self.signal = signal
        self.hangouts = hangouts
        self.deleted = deleted

    def __str__(self) -> str:
        return f'{self.phone_privat} {self.email_privat} {self.whatsup} {self.telegram} {self.signal} {self.hangouts} {self.phone_work} {self.phone_secret} {self.email_work} {self.email_secret}'

    def __repr__(self) -> str:
        return self._str_()


class NetworkElement:
    def __init__(self, contact:Contact, connection:Connection):
        self.contact = contact
        self.connection = connection

    def __str__(self) -> str:
        return f"{self.contact} {self.connection}"

    def __repr__(self) -> str:
        return self._str_()

def create_connection(db_file):
    conn = None;
    try:
        conn = sqlite3.connect(db_file) # creates a file-based database
        return conn
    except Error as e:
        print(e)

def create_table(conn, create_table_sql):
    try:
        cursor = conn.cursor()
        cursor.execute(create_table_sql)
    except Error as e:
        print(e)
    finally:
        cursor.close()

def create_network_element(conn, network_element) -> int:
    sql = ''' INSERT INTO contacts(name,surname,birthdate,note, deleted)
              VALUES(?,?,?,?,?) '''
    try:
        cur = conn.cursor()
        cur.execute(sql, (network_element.contact.name, network_element.contact.surname, network_element.contact.birthdate, network_element.contact.note, network_element.contact.deleted))
        contact_id = cur.lastrowid

        sql = ''' INSERT INTO connections(id_contact,phone_privat,phone_work,phone_secret,email_privat,email_work,email_secret,whatsup,telegram,signal,hangouts, deleted)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?) '''
        cur.execute(sql, (contact_id, network_element.connection.phone_privat, network_element.connection.phone_work, network_element.connection.phone_secret, network_element.connection.email_privat, network_element.connection.email_work, network_element.connection.email_secret, network_element.connection.whatsup, network_element.connection.telegram, network_element.connection.signal, network_element.connection.hangouts, network_element.connection.deleted))        
        return cur.lastrowid
    finally:
        cur.close()
        conn.commit()

def get_contacts_by_name_and_surname(connection: Connection, name=None, surname=None):
    try:
        cursor = connection.cursor()
        query = "SELECT * FROM contacts WHERE 1=1 AND deleted = 0 "
        params = []

        if name:
            query += " AND name LIKE ?"
            params.append('%' + name + '%')

        if surname:
            query += " AND surname LIKE ?"
            params.append('%' + surname + '%')

        cursor.execute(query, params)

        contacts = []
        for row in cursor: # cursor.fetchall():
            contact = Contact(row[0], row[1], row[2], row[3], row[4])
            contacts.append(contact)

        return contacts
    finally:
        cursor.close()

def get_network_element(conn, id) -> Union[NetworkElement, None]:
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM contacts WHERE id=?", (id,))

        row = cur.fetchone()
        if row is None:
            return None
        contact = Contact(row[0], row[1], row[2], row[3], row[4], row[5])

        cur.execute("SELECT * FROM connections WHERE id_contact=?", (id,))
        row = cur.fetchone()
        connection = Connection(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12])

        return NetworkElement(contact, connection)
    finally:
        cur.close()

def update_network_element(conn, network_element):
    sql_contacts = ''' UPDATE contacts
              SET name = ? ,
                  surname = ? ,
                  birthdate = ? ,
                  note = ?,
                  deleted = ?
              WHERE id = ?'''
    sql_connections = ''' UPDATE connections
            SET phone_privat = ? ,
                phone_work = ? ,
                phone_secret = ? ,
                email_privat = ? ,
                email_work = ? ,
                email_secret = ? ,
                whatsup = ? ,
                telegram = ? ,
                signal = ? ,
                hangouts = ?, 
                deleted = ?
            WHERE id_contact = ?'''

    try:
        cur =  conn.cursor()
        cur.execute(sql_contacts, 
                    (network_element.contact.name, 
                     network_element.contact.surname, 
                     network_element.contact.birthdate, 
                     network_element.contact.note, 
                     network_element.contact.deleted, 
                     network_element.contact.id
                     ))

        cur.execute(sql_connections, 
                    (network_element.connection.phone_privat, 
                     network_element.connection.phone_work, 
                     network_element.connection.phone_secret, 
                     network_element.connection.email_privat, 
                     network_element.connection.email_work, 
                     network_element.connection.email_secret, 
                     network_element.connection.whatsup, 
                     network_element.connection.telegram, 
                     network_element.connection.signal, 
                     network_element.connection.hangouts, 
                     network_element.connection.deleted, 
                     network_element.contact.id))
    finally:
        cur.close()
        conn.commit()

def delete_network_element(conn, id):
    try:
        cur = conn.cursor()
        element = get_network_element(conn, id)
        if element:
            element.contact.deleted = True
            element.connection.deleted = True
            update_network_element(conn, element)
    finally:
        cur.close()
        conn.commit()


def init_database(connection: Connection) -> bool:
    # DATE - text in format 'YYYY-MM-DD'
    sql_create_contacts_table = """ CREATE TABLE IF NOT EXISTS contacts (
                                        id integer PRIMARY KEY AUTOINCREMENT,
                                        name text NOT NULL,
                                        surname text NOT NULL,
                                        birthdate DATE,
                                        note text, 
                                        deleted boolean DEFAULT FALSE
                                    ); """

    sql_create_connections_table = """CREATE TABLE IF NOT EXISTS connections (
                                    id integer PRIMARY KEY AUTOINCREMENT,
                                    id_contact integer NOT NULL,
                                    phone_privat text,
                                    phone_work text,
                                    phone_secret text,
                                    email_privat text,
                                    email_work text,
                                    email_secret text,
                                    whatsup text,
                                    telegram text,
                                    signal text,
                                    hangouts text,
                                    deleted boolean DEFAULT FALSE, 
                                    FOREIGN KEY (id_contact) REFERENCES contacts (id)
                                );"""
    if connection is not None:
        create_table(connection, sql_create_contacts_table)
        create_table(connection, sql_create_connections_table)
        return True
    else:
        print("Error! cannot create the database connection.")
        return False


class DateValidator(Validator):
    def validate(self, document):
        try:
            datetime.strptime(document.text, '%Y-%m-%d')
        except ValueError:
            raise ValidationError(
                message='Please enter a date in YYYY-MM-DD format',
                cursor_position=len(document.text))

class EmailValidator(Validator):
    def validate(self, document):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", document.text):
            raise ValidationError(
                message='Please enter a valid email address',
                cursor_position=len(document.text))

class PhoneValidator(Validator):
    def validate(self, document):
        if not re.match(r"(\+)?\d{4,}", document.text):
            raise ValidationError(
                message='Please enter a valid phone number',
                cursor_position=len(document.text))

def prompt_network_element(element: NetworkElement = None):
    contact_questions = [
        {
            'type': 'input',
            'name': 'name',
            'message': 'Enter the contact\'s name:',
            'default': element.contact.name if element else ''
        },
        {
            'type': 'input',
            'name': 'surname',
            'message': 'Enter the contact\'s surname:',
            'default': element.contact.surname if element else ''
        },
        {
            'type': 'input',
            'name': 'birthdate',
            'message': 'Enter the contact\'s birthdate (YYYY-MM-DD):',
            'validate': DateValidator,
            'default': element.contact.birthdate if element else ''
        },
        {
            'type': 'input',
            'name': 'note',
            'message': 'Enter a note for the contact:',
            'default': element.contact.note if element else ''
        }
    ]

    connection_questions = [
        {
            'type': 'input',
            'name': 'phone_privat',
            'message': 'Enter the private phone number:',
            'default': element.connection.phone_privat if element else '',
        },
        {
            'type': 'input',
            'name': 'phone_work',
            'message': 'Enter the work phone number:',
            'default': element.connection.phone_work if element else '',
        },
        {
            'type': 'input',
            'name': 'email_privat',
            'message': 'Enter the private email:',
            'validate': EmailValidator,
            'default': element.connection.email_privat if element else '',  
        },
        {
            'type': 'input',
            'name': 'email_work',
            'message': 'Enter the work email (optional):',
            'default': element.connection.email_work if element else '',
        },
        # Add more questions for the remaining fields
    ]

    contact_answers = prompt(contact_questions)
    connection_answers = prompt(connection_questions)

    contact = Contact(0, contact_answers['name'], contact_answers['surname'], contact_answers['birthdate'], contact_answers['note'])
    connection = Connection(0, 0, connection_answers['phone_privat'], connection_answers['phone_work'], '', connection_answers['email_privat'], connection_answers['email_work'] or '', '', '', '', '', '')

    return NetworkElement(contact, connection)

main_menu: List = [
    'Find record',
    'Create record',
    'Edit record',
    'Import Google contacts',
    'Delete record',
    'Exit'
]


def confirm_delete(element: NetworkElement):
    questions = [
        {
            'type': 'confirm',
            'name': 'confirm',
            'message': f"Do you really want to delete ({element.contact.name}, {element.contact.surname}) ?",
            'default': False
        }
    ]

    answers = prompt(questions)
    return answers['confirm']

class GoogleContact:
    def __init__(self, name, surname, phone1, phone2, phone3, email1, email2, email3, birthdate=None, note=None):
        self.name = name
        self.surname = surname
        self.phone1 = phone1
        self.phone2 = phone2
        self.phone3 = phone3
        self.email1 = email1
        self.email2 = email2
        self.email3 = email3
        self.birthdate = birthdate
        self.note = note
    
    def __str__(self) -> str:
        return f'{self.name} {self.surname} {self.email} {self.phone} {self.birthdate} {self.note}'
    
    def __repr__(self) -> str:
        return self._str_()

google_contact_columns=["Name","Given Name","Additional Name","Family Name","Yomi Name","Given Name Yomi","Additional Name Yomi","Family Name Yomi","Name Prefix","Name Suffix","Initials","Nickname","Short Name","Maiden Name","Birthday","Gender","Location","Billing Information","Directory Server","Mileage","Occupation","Hobby","Sensitivity","Priority","Subject","Notes","Language","Photo","Group Membership","E-mail 1 - Type","E-mail 1 - Value","E-mail 2 - Type","E-mail 2 - Value","IM 1 - Type","IM 1 - Service","IM 1 - Value","Phone 1 - Type","Phone 1 - Value","Phone 2 - Type","Phone 2 - Value","Phone 3 - Type","Phone 3 - Value","Phone 4 - Type","Phone 4 - Value","Phone 5 - Type","Phone 5 - Value","Address 1 - Type","Address 1 - Formatted","Address 1 - Street","Address 1 - City","Address 1 - PO Box","Address 1 - Region","Address 1 - Postal Code","Address 1 - Country","Address 1 - Extended Address","Address 2 - Type","Address 2 - Formatted","Address 2 - Street","Address 2 - City","Address 2  - PO Box","Address 2 - Region","Address 2 - Postal Code","Address 2 - Country","Address 2 - Extended Address","Organization 1 - Type","Organization 1 - Name","Organization 1 - Yomi Name","Organization 1 - Title","Organization 1 - Department","Organization 1 - Symbol","Organization 1 - Location","Organization  1 - Job Description","Website 1 - Type","Website 1 - Value"]

def parse_google_contacts(file_path: str) -> List[GoogleContact]:
    contacts = []
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header row
        for row in reader:
            contact = GoogleContact(
                name=row[google_contact_columns.index('Name')],
                surname=row[google_contact_columns.index('Given Name')]+" "+row[google_contact_columns.index('Additional Name')]+" "+row[google_contact_columns.index('Family Name')], 
                phone1=row[google_contact_columns.index('Phone 1 - Value')],
                phone2=row[google_contact_columns.index('Phone 2 - Value')],
                phone3=row[google_contact_columns.index('Phone 3 - Value')],
                email1=row[google_contact_columns.index('E-mail 1 - Value')],
                email2=row[google_contact_columns.index('E-mail 2 - Value')],
                email3="",
                birthdate=row[google_contact_columns.index('Birthday')],
                note=row[google_contact_columns.index('Notes')]
            )
            contacts.append(contact)
    return contacts


def menu():
    questions = [
        {
            'type': 'list',
            'name': 'action',
            'message': 'What do you want to do?',
            'choices': main_menu
        }
    ]

    answers = prompt(questions)
    return answers['action']

def print_contacts(contacts):
# from tabulate import tabulate
#    table: List[List[str]] = []
#    for contact in contacts:
#        each_row = [contact.id, contact.name, contact.surname, contact.birthdate, contact.note]
#        table.append(each_row)
#    print(tabulate(table, headers=["ID", "Name", "Surname", "Birthdate", "Note"]))

    table = Table(show_header=True, header_style="bold green")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Surname")
    table.add_column("Birthdate")
    table.add_column("Note")

    for contact in contacts:
        table.add_row(str(contact.id), contact.name, contact.surname, str(contact.birthdate), contact.note)

    console = Console()
    console.print(table)

def print_network_element(network_elements:List[NetworkElement]) -> None:
    table = Table(show_header=True, header_style="bold green")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Surname")
    table.add_column("Birthdate")
    table.add_column("Note")
    table.add_column("Phone privat")
    table.add_column("Phone work")
    table.add_column("Phone secret")
    table.add_column("Email privat")
    table.add_column("Email work")
    table.add_column("Email secret")
    table.add_column("Whatsup")
    table.add_column("Telegram")
    table.add_column("Signal")
    table.add_column("Hangouts")

    for element in network_elements:
        table.add_row(str(element.contact.id), 
                      element.contact.name, 
                      element.contact.surname, 
                      str(element.contact.birthdate), 
                      element.contact.note,
                      element.connection.phone_privat,
                      element.connection.phone_work,
                      element.connection.phone_secret,
                      element.connection.email_privat,
                      element.connection.email_work,
                      element.connection.email_secret,
                      element.connection.whatsup,
                      element.connection.telegram,
                      element.connection.signal,
                      element.connection.hangouts)
    console = Console()
    console.print(table)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        database = sys.argv[1]
    else:
        database = DB_DEFAULT_PATH

    with create_connection(database) as connection:
        init_database(connection)

        while True:
            mode: str = menu()
            if mode == 'Exit':
                sys.exit(0)
                
            if mode == 'Create record':
                print("-------------")
                element: NetworkElement = prompt_network_element()
                id = create_network_element(connection, element)
                print(f" created: {id}")
                print(get_network_element(connection, id))

            if mode == 'Edit record':
                print("-------------")
                id = input("Enter the ID of the record you want to edit: ")
                element = get_network_element(connection, id)
                print(element)
                element = prompt_network_element(element)
                element.contact.id = id
                update_network_element(connection, element)
                print(get_network_element(connection, id))
            
            if mode == 'Delete record':
                print("-------------")
                id = input("Enter the ID of the record you want to delete: ")
                element:NetworkElement = get_network_element(connection, id)
                if not element:
                    print_rich(f"[bold yellow]Warning: [/bold yellow] element ({id}) was not found.")
                    continue
                if confirm_delete(element):
                    delete_network_element(connection, id)
                    print("Deleted")

            if mode == 'Find record':
                print("-------------")
                name = input("Enter the name of the contact you want to find: ")
                surname = input("Enter the surname of the contact you want to find: ")
                contacts = get_contacts_by_name_and_surname(connection, name, surname)
                if not contacts:
                    print_rich(f"[bold yellow]Warning: [/bold yellow] element ({name} {surname}) was not found.")
                else:
                    # print_contacts(contacts)
                    print_network_element([get_network_element(connection, contact.id) for contact in contacts])

            if mode == 'Import Google contacts':
                print("-------------")
                path_to_file = input("Enter full path to csv file with Google contacts: ")
                contacts: List[GoogleContact] = parse_google_contacts(path_to_file)
                for contact in contacts:
                    element = NetworkElement(Contact(0, contact.name, contact.surname, contact.birthdate, contact.note), 
                                             Connection(0, 0, contact.phone1, contact.phone2, contact.phone3, contact.email1, contact.email2, contact.email3, '', '', '', ''))
                    create_network_element(connection, element)