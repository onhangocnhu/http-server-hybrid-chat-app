import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

users = [("admin", "secret"), ("peer1", "1234"), ("peer2", "1234"), ("peer3", "1234"), ("peer4", "1234"), ("peer5", "1234")]
for u, p in users:
    try:
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (u, p))
    except sqlite3.IntegrityError:
        pass

conn.commit()
conn.close()
print("[DB] Initialized with default users.")
