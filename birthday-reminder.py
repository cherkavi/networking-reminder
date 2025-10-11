import sys
import datetime
from _common import create_table, create_connection, Connection, NetworkElement, Contact, DB_DEFAULT_PATH, get_contacts_by_name_and_surname

def get_recent_and_upcoming_birthdays(connection: Connection, days_range=5):    
    today = datetime.date.today()
    results = []

    for delta in range(-days_range, days_range + 1):
        target_date = today + datetime.timedelta(days=delta)
        # We only care about month and day, not year
        month = target_date.month
        day = target_date.day

        query = """
            SELECT * FROM contacts WHERE strftime('%m-%d', birthdate) = ? AND deleted IS NOT TRUE
        """
        cursor = connection.cursor()
        try:
            cursor.execute(query, (f"{month:02d}-{day:02d}",))
            contacts = cursor.fetchall()
            for contact in contacts:
                results.append({
                    "contact": contact,
                    "days_from_today": delta
                })
        except Exception as e:
            print(f"DB path is not right ")
            return []
        finally:
            cursor.close()
    return results

# Example usage:
if __name__ == '__main__':
    if len(sys.argv) > 1:
        database = sys.argv[1]
    else:
        database = DB_DEFAULT_PATH

    with create_connection(database) as connection:
        birthdays = get_recent_and_upcoming_birthdays(connection, 5)
        for entry in birthdays:
            contact = entry["contact"]
            days = entry["days_from_today"]
            if days > 0:
                color = "\033[1;32m"  # Bold green
            elif days < 0:
                color = "\033[1;31m"  # Bold red
            else:
                color = "\033[1m"     # Bold (default color)
            reset = "\033[0m"
            print(f"{color}{days}{reset} - {contact[3]} - {contact[1]} {contact[2]} ")

