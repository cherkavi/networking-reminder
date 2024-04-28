# application for managing your network ( people around you )

## contact-manager DB description 
manage your contacts ( Entity 'Contact' ) in Database:
* name
* surname
* birthdate
* note
* deleted

with connections ( Entity 'Connection' ) in Database
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

## Database direct connection
```sql
-- sqlite3 contacts-meetings.db

select * from contacts;
select * from connections;
```

```sh
# rm contacts-meetings.db 
python3 contacts-manager.py contacts-meetings.db
```