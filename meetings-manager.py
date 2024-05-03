import sys
import threading
from datetime import datetime, timedelta
from sqlite3 import Connection
from typing import List, Union, Tuple

from questionary import prompt, Separator, unsafe_prompt, Style, press_any_key_to_continue
from rich.console import Console
from rich.table import Table

from _common import create_table, create_connection, DB_DEFAULT_PATH, Meeting, get_contacts_by_name_and_surname, \
    Contact, Status


def create_meeting(connection: Connection, meeting: Meeting) -> Meeting:
    """ create meeting and return the same object but with newly created id"""
    if connection is None:
        return False
    cursor = connection.cursor()
    try:
        cursor.execute("INSERT INTO meetings (id_contact, date, status, notes) VALUES (?, ?, ?, ?)",
                       (meeting.id_contact, meeting.date, meeting.status.value, meeting.notes))
        connection.commit()
        meeting.id = cursor.lastrowid
    finally:
        cursor.close()
    return meeting


def update_meeting(connection: Connection, meeting: Meeting) -> None:
    """ update meeting  or throw exception """
    if connection is None:
        return False
    cursor = connection.cursor()    
    try:
        cursor.execute("UPDATE meetings SET id_contact=?, date=?, status=?, notes=? WHERE id=?",
                       (meeting.id_contact, meeting.date, meeting.status.value, meeting.notes, meeting.id))
        connection.commit()
    finally:
        cursor.close()


def init_database(connection: Connection) -> bool:
    """ create tables if not exists """
    if connection is None:
        return False
    create_table(connection,
                 """
                 CREATE TABLE IF NOT EXISTS 
                 meetings (
                     id INTEGER PRIMARY KEY, 
                     id_contact INTEGER, 
                     date DATE, 
                     status INTEGER, 
                     notes TEXT,
                     FOREIGN KEY (id_contact) REFERENCES contacts (id)
                     )
                """)
    return True


def main_menu():
    questions = [
        {
            'type': 'list',
            'name': 'main_menu',
            'message': 'Main Menu:',
            'choices': ['Upcoming Meetings ( till tomorrow )', 'Find person', 'Find All persons without meetings', Separator(), 'Exit']
        }
    ]
    try:
        return unsafe_prompt(questions)['main_menu']
    except KeyboardInterrupt:
        return "Exit"


def person_menu(person_name: str) -> str:
    questions = [
        {
            'type': 'list',
            'name': 'contact_menu',
            'message': f"Person: {person_name}",
            'choices': ['Show next meeting',
                        'Create new meeting',
                        'Show last 5 meetings',
                        Separator(),
                        'Go back']
        }
    ]
    try:
        return unsafe_prompt(questions, style=Style([('question', 'fg:red')]))['contact_menu']
    except KeyboardInterrupt:
        return "Go back"


def edit_meeting_menu():
    questions = [
        {
            'type': 'list',
            'name': 'edit_meeting_menu',
            'message': 'What do you want to do?',
            'choices': ['Set as done', 'Set as cancelled', 'Set as callback', 'Create new next meeting', Separator(),
                        'Go back']
        }
    ]
    return prompt(questions)['edit_meeting_menu']


def select_one_contact(contacts: List[Contact]) -> Union[Contact, None]:
    choices = [{'name': f'{contact.name} {contact.surname}', 'value': contact.id} for contact in contacts]
    choices.insert(0, 'Go back')
    choices.insert(1, Separator())

    questions = [
        {
            'type': 'list',
            'name': 'contact_menu',
            'message': 'Select a contact:',
            'choices': choices
        }
    ]
    try:
        contact_id: int = unsafe_prompt(questions)['contact_menu']
        return Contact.get_by_id(contacts, contact_id)
    except KeyboardInterrupt:
        return None


def find_contact_menu(contacts) -> int:
    """
    :param contacts:
    :return: contact id
    """
    questions = [
        {
            'type': 'input',
            'name': 'name',
            'message': 'Enter name of the contact:',
        },
        {
            'type': 'input',
            'name': 'surname',
            'message': 'Enter surname of the contact:',
        }
    ]
    try:
        answers = unsafe_prompt(questions)
    except KeyboardInterrupt:
        return None

    name = answers['name']
    surname = answers['surname']
    contacts: List[Contact] = get_contacts_by_name_and_surname(connection, name, surname)

    return select_one_contact(contacts)


def check_date_format(date: str) -> bool:
    # datetime.strptime(x, '%Y-%m-%d') # or 'Invalid date format, should be YYYY-MM-DD'
    try:
        datetime.strptime(date, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def meeting_menu(meeting: Meeting) -> Meeting:
    questions = [
        {
            'type': 'input',
            'name': 'date',
            'message': 'Enter date (YYYY-MM-DD):',
            'default': meeting.date.strftime('%Y-%m-%d'),
            'validate': lambda x: check_date_format(x)
        },
        {
            'type': 'list',
            'name': 'status',
            'message': 'Select status:',
            'choices': [e.name for e in Status],
            'default': meeting.status.name if meeting and meeting.status else None,
            # 'validate': lambda x: x in [e.name for e in Status]
        },
        {
            'type': 'input',
            'name': 'notes',
            'message': 'Enter notes:',
            # DO NOT return None as default
            'default': meeting.notes if meeting and meeting.notes else ""
        }
    ]
    try:
        answers = unsafe_prompt(questions)
        return Meeting(meeting.id_contact,
                       datetime.strptime(answers['date'], '%Y-%m-%d'),
                       Status[answers['status']],
                       answers['notes'],
                       meeting.id)
    except KeyboardInterrupt:
        return None


def save_meeting(connection: Connection, new_meeting: Meeting) -> Meeting:
    if new_meeting.id:
        update_meeting(connection, new_meeting)
        return new_meeting
    else:
        return create_meeting(connection, new_meeting)


def get_todo_meeting_by_contact_id(connection: Connection, contact_id: int):
    cursor = connection.cursor()
    try:
        cursor.execute(
            "SELECT id_contact, date, status, notes, id FROM meetings WHERE id_contact=? AND status=?  order by DATE ASC",
            (contact_id, Status.TODO.value))
        return [Meeting(id_contact=row[0],
                        date=datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S'),
                        status=Status(row[2]),
                        notes=row[3],
                        id=row[4]
                        ) for row in cursor.fetchall()]
    finally:
        cursor.close()


def get_meetings_by_contact_id(connection: Connection, contact_id: int, size: int):
    cursor = connection.cursor()
    try:
        cursor.execute(
            "SELECT id_contact, date, status, notes, id FROM meetings WHERE id_contact=? order by DATE ASC  LIMIT ?",
            (contact_id, size))
        return [Meeting(id_contact=row[0],
                        date=datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S'),
                        status=Status(row[2]),
                        notes=row[3],
                        id=row[4]
                        ) for row in cursor.fetchall()]
    finally:
        cursor.close()


def select_one_meeting(meetings: List[Meeting]) -> Union[int, None]:
    if not meetings:
        return None
    questions = [
        {
            'type': 'list',
            'name': 'meeting',
            'message': 'Select a meeting for editing:',
            'choices': [{"name": f'{meeting.date} - {meeting.notes}', "value": meeting.id} for meeting in meetings]
        }
    ]
    try:
        meeting_id: int = unsafe_prompt(questions)['meeting']
    except KeyboardInterrupt:
        return None
    if meeting_id:
        return Meeting.get_by_id(meetings, meeting_id)
    else:
        return None


def print_list_of_meetings(meetings: List[Meeting]) -> None:
    table = Table(show_header=True, header_style="bold green")
    table.add_column("Date")
    table.add_column("Status")
    table.add_column("Notes")
    for meeting in meetings:
        table.add_row(meeting.date.strftime('%Y-%m-%d'),
                      Status(meeting.status.value).name,
                      meeting.notes)
    console = Console()
    console.print(table)


def find_upcoming_meetings(connection: Connection, control_date: datetime) -> List[Tuple[Meeting, Contact]]:
    cursor = connection.cursor()
    try:
        cursor.execute(
            """ 
            SELECT m.id_contact, m.date, m.status, m.notes, m.id,
                   c.id, c.name, c.surname, c.birthdate, c.note 
            FROM meetings m inner join contacts c on m.id_contact = c.id  
            WHERE m.status<? and m.date < ? order by m.DATE ASC
            """,
            (Status.DONE.value, control_date,))
        result = [(Meeting(id_contact=row[0],
                           date=datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S'),
                           status=Status(row[2]),
                           notes=row[3],
                           id=row[4]
                           ),
                   Contact(
                       id=row[5],
                       name=row[6],
                       surname=row[7],
                       birthdate=row[8],
                       note=row[9]
                   )) for row in cursor.fetchall()]
        if not result or len(result) == 0:
            return None
        else:
            return result
    finally:
        cursor.close()


def print_contact(connection: Connection, id_contact: int) -> None:
    cursor = connection.cursor()
    try:
        cursor.execute("""SELECT contacts.name, contacts.surname, contacts.birthdate, contacts.note,
                                connections.phone_privat, connections.phone_work, connections.phone_secret, 
                                connections.email_privat, connections.email_work, connections.email_secret, 
                                connections.whatsup, connections.telegram, connections.signal, connections.hangouts 
                               FROM contacts inner join connections on contacts.id = connections.id_contact WHERE contacts.id=? """,
                       (id_contact,))
        row = cursor.fetchone()

        console = Console()

        table = Table(show_header=True, header_style="bold green")
        table.add_column("Name")
        table.add_column("Surname")
        table.add_column("Birthday")
        table.add_column("Note")
        table.add_row(row[0], row[1], row[2], row[3])
        console.print(table)

        table = Table(show_header=True, header_style="bold green")
        table.add_column("Phone")
        table.add_column("EMail")
        table.add_column("IM")
        table.add_row(row[4], row[7], "w:" + row[10])
        table.add_row(row[5], row[8], "t:" + row[11])
        table.add_row(row[6], row[9], "s:" + row[12])
        table.add_row("", "", "h:" + row[13])
        console.print(table)

    finally:
        cursor.close()


def select_one_meeting_with_contacts(meetings: List[Tuple[Meeting, Contact]]) -> Union[Meeting, None]:
    if not meetings:
        return None
    questions = [
        {
            'type': 'list',
            'name': 'meeting',
            'message': 'Select a meeting for editing:',
            'choices': [{"name": f'{meeting.date} - {contact.name} {contact.surname}', "value": meeting.id} for meeting, contact in meetings]
        }
    ]
    try:
        meeting_id: int = unsafe_prompt(questions)['meeting']
    except KeyboardInterrupt:
        return None
    if meeting_id:
        return Meeting.get_by_id([meeting for meeting, _ in meetings], meeting_id)
    else:
        return None


def find_contacts_without_meetings(connection: Connection) -> List[Contact]:
    cursor = connection.cursor()
    try:
        cursor.execute(
            """ 
            SELECT c.id, c.name, c.surname, c.birthdate, c.note
            FROM contacts c            
            WHERE c.id not in (SELECT id_contact FROM meetings where id_contact is not null) and c.deleted = 0
            """)
        return [Contact(id=row[0],
                        name=row[1],
                        surname=row[2],
                        birthdate=row[3],
                        note=row[4]
                        ) for row in cursor.fetchall()]
    finally:
        cursor.close()


def show_menu(connection: Connection):
    while True:
        ##########################################################
        choice = main_menu()
        if choice == 'Exit':
            break
        elif choice == 'Upcoming Meetings ( till tomorrow )':
            # datetime.now() + timedelta(days=5)
            meetings: List[(Meeting, Contact)] = find_upcoming_meetings(connection, datetime.now() + timedelta(days=2))
            if meetings is None:
                continue
            selected_meeting = select_one_meeting_with_contacts(meetings)
            if selected_meeting:
                print_contact(connection, selected_meeting.id_contact)
                updated_meeting: Meeting = meeting_menu(selected_meeting)
                if updated_meeting:
                    update_meeting(connection, updated_meeting)
                    press_any_key_to_continue(message="saved...").ask()
                else:
                    continue
            else:
                continue
        elif choice == 'Find All persons without meetings':
            contacts: List[Contact] = find_contacts_without_meetings(connection)
            if not contacts:
                print(f"contacts: {contacts}")
                continue
            contact: Contact = select_one_contact(contacts)
            if contact:
                print_contact(connection, contact.id)
                five_days_later = datetime.now() + timedelta(days=5)
                meeting = Meeting(contact.id, five_days_later, Status.TODO)
                print("  Create new Meeting: ")
                new_meeting: Meeting = meeting_menu(meeting)
                if new_meeting:
                    save_meeting(connection, new_meeting)
                else:
                    continue
            else:
                continue
        elif choice == 'Find person':
            contact: Contact = find_contact_menu(connection)
            if contact is None:
                continue
            print_contact(connection, contact.id)

            ##########################################################
            while True:
                contact_choice = person_menu(f"{contact.name} {contact.surname}")
                if contact_choice == 'Go back':
                    break
                elif contact_choice == 'Show next meeting':
                    meetings: List[Meeting] = get_todo_meeting_by_contact_id(connection, contact.id)
                    selected_meeting = select_one_meeting(meetings)
                    if selected_meeting:
                        updated_meeting: Meeting = meeting_menu(selected_meeting)
                        if updated_meeting:
                            update_meeting(connection, updated_meeting)
                        else:
                            continue
                elif contact_choice == 'Create new meeting':
                    five_days_later = datetime.now() + timedelta(days=5)
                    meeting = Meeting(contact.id, five_days_later, Status.TODO)
                    new_meeting: Meeting = meeting_menu(meeting)
                    if new_meeting:
                        save_meeting(connection, new_meeting)
                elif contact_choice == 'Show last 5 meetings':
                    meetings: List[Meeting] = get_meetings_by_contact_id(connection, contact.id, 5)
                    print_list_of_meetings(meetings)
                elif contact_choice == 'Edit next meeting':
                    ##########################################################
                    while True:
                        edit_meeting_choice = edit_meeting_menu()
                        if edit_meeting_choice == 'Go back':
                            break
                        # "set meeting status " Handle other choices here
                # "after finding the contact" Handle other choices here
        # "find contact" Handle other choices here


def escape_listener():
    def on_press(key):
        if key == keyboard.Key.esc:
            # print('Escape key pressed. Exiting...')
            controller = Controller()
            # Press and release Ctrl+C
            controller.press(Key.ctrl)
            controller.press('c')
            controller.release('c')
            controller.release(Key.ctrl)
            return True

    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        database = sys.argv[1]
    else:
        database = DB_DEFAULT_PATH

    if "activate_escape" in sys.argv:
        escape_to_break_converter = threading.Thread(target=escape_listener)
        escape_to_break_converter.daemon = True
        escape_to_break_converter.start()

    with create_connection(database) as connection:
        if not init_database(connection):
            exit(1)
        show_menu(connection)
