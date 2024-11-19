from .models import db
from pony.orm import Database

def configure_database():
    db.bind(
        provider='postgres',
        user='postgres',
        password='password',
        host='172.18.7.85',
        database='schedulingalgo'
    )
    db.generate_mapping(create_tables=True)

# configure_database()