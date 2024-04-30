# application for managing your network ( people around you )
[Main Idea and inspiration](https://www.youtube.com/watch?v=yezuJEaEOpg&t=368s)

## Installation 

### python libraries
```sh
pip3 install questionary rich SQLite3-0611
```

### sqlite driver/cli
> only in case of direct connection 
```sh
sudo apt install sqlite3
```
### reset DB 
```sh
PATH_TO_DB=./contacts-meetings.db
rm $PATH_TO_DB
```

### specify path to DB ( place for the Database file )
```sh
# specify network file system ( or Dropbox ) - can be empty/not-exist
PATH_TO_DB=./contacts-meetings.db
```

## Usage

### Contacts manager 
```sh
PATH_TO_DB=./contacts-meetings.db
python3 contacts-manager.py $PATH_TO_DB
```

#### create contact
select menu 'Create record'

#### edit contact
select menu 'Edit record'  
enter id of the contact ( search it with find )  

#### delete contact
select menu 'Delete record'  
enter id of the contact ( search it with find )  

#### import contact from Google export
1. go to your [google contacts](https://contacts.google.com/)
2. header of the table (Name, Email, Phone number, Job title & Company ... ) has also "printer" and "export" buttons
3. click on export icon
4. "Export as" : "Google CSV"
5. Export
6. remember full path to the downloaded file with your contacts
7. in application, select menu "Import Google contacts"
8. enter full path to exported csv file from step #6

### Meeting manager 
```sh
PATH_TO_DB=./contacts-meetings.db
python3 meetings-manager.py $PATH_TO_DB
```

#### create next meeting
1. select "Find person" 
2. enter part of the name ( or empty )
3. enter part of the surname ( or empty )
4. select record
5. enter Date, Status ( TODO ), Note ( or empty )
   
#### how to see upcoming meetings
select menu "Upcoming Meetings"
if no meetings - menu will show nothing and print out "Main Menu"
if you will select the meeting - "edit meeting" will be activated

#### find contacts without upcoming meeting
select menu 

## Technical description 
Two tier application ( DB + Python console app).

### contact-manager DB description 
manage your contacts ( Entity 'Contacts' ) in Database:
* name
* surname
* birthdate
* note
* deleted

with connections ( Entity 'Connections' ) in Database
* phone_privat
* phone_work
* phone_secret
* email_privat
* email_work
* email_secret
* whatsup
* telegram
* signal
* hangouts
* deleted


and meetings ( Entity "Meetings" ) in Database
* id_contact 
* date (in format "%Y-%m-%d %H:%M:%S")
* status (0..99)
* notes

### Database direct connection
```sh
PATH_TO_DB=./contacts-meetings.db
sqlite3 $PATH_TO_DB
```
```sql
select * from contacts limit 5;
select * from connections limit 5 ;

select * from meetings limit 5;
```

