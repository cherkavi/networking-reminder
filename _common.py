import sqlite3
from sqlite3 import Connection, Error
from datetime import datetime
from enum import Enum
from typing import List


DB_DEFAULT_PATH = "contacts-meetings.db"
""" default path to database file """


def create_table(conn: Connection, create_table_sql):
    try:
        cursor = conn.cursor()
        cursor.execute(create_table_sql)
    except Error as e:
        print(e)
    finally:
        cursor.close()


def create_connection(db_file: str = DB_DEFAULT_PATH):
    conn = None;
    try:
        conn = sqlite3.connect(db_file)  # creates a file-based database
        return conn
    except Error as e:
        print(e)


class Contact:
    def __init__(self, id, name, surname, birthdate, note, deleted=False):
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

    @staticmethod
    def get_by_id(contacts, contact_id):
        for contact in contacts:
            if contact.id == contact_id:
                return contact
        return None


class Connection:
    def __init__(self, id, id_contact, phone_privat, phone_work, phone_secret, email_privat, email_work, email_secret,
                 whatsup, telegram, signal, hangouts, deleted=False):
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
    def __init__(self, contact: Contact, connection: Connection):
        self.contact = contact
        self.connection = connection

    def __str__(self) -> str:
        return f"{self.contact} {self.connection}"

    def __repr__(self) -> str:
        return self._str_()

class Status(Enum):
    TODO = 0
    """ init status of the meeting - need to work on it """
    DONE = 20
    """ meeting is done """
    CANCELLED = 40
    """ meeting is cancelled by some reason, 'note' can have the reason """
    CALLBACK = 60



class Meeting:
    def __init__(self, id_contact: int, date: datetime, status: Status, notes: str = None, id: int = None):
        self.id = id
        """ id of the meeting from db:meetings.id """
        self.id_contact = id_contact
        """ FK to contacts.id """
        self.date: datetime = date
        self.status: Status = status
        self.notes = notes

    def __str__(self):
        return f"Meeting {self.id_contact} on {self.date} status: {self.status} notes: {self.notes}"

    @staticmethod
    def get_by_id(meetings: List, meeting_id: int):
        for meeting in meetings:
            if meeting.id == meeting_id:
                return meeting
        return None


def get_contacts_by_name_and_surname(connection: Connection, name=None, surname=None) -> List[Contact]:
    """
    get contacts by name and surname
    :param connection:
    :param name: part of the name '*name*'
    :param surname: part of the surname '*surname*'
    :return: list of contacts
    """
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

        contacts: List[Contact] = []
        for row in cursor:  # cursor.fetchall():
            contact = Contact(row[0], row[1], row[2], row[3], row[4])
            contacts.append(contact)

        return contacts
    finally:
        cursor.close()


class GoBack(Exception):
    pass

def throw_go_back():
    raise GoBack()