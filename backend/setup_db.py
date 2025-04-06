import sqlite3
import os

# Define the path for the database file
db_path = os.path.join(os.getcwd(), "jobs.db")

# Define the schema for the jobs table
create_table_query = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    state TEXT,
    title TEXT,
    pay TEXT,
    deadline TEXT,
    link TEXT UNIQUE
);
"""

# Connect to the database and create the table
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute(create_table_query)
conn.commit()
conn.close()

print("Database and table created successfully!")
