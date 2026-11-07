import db


def list_members():
    conn = db.connect()
    rows = conn.execute("SELECT * FROM members").fetchall()
    conn.close()
    return rows


def get_member(member_id):
    conn = db.connect()
    row = conn.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()
    conn.close()
    return row


def get_member_by_email(email):
    conn = db.connect()
    row = conn.execute("SELECT * FROM members WHERE email = ?", (email,)).fetchone()
    conn.close()
    return row


def create_member(name, email, member_type):
    conn = db.connect()
    cur = conn.execute("INSERT INTO members (name, email, type) VALUES (?, ?, ?)", (name, email, member_type))
    conn.commit()
    row = conn.execute("SELECT * FROM members WHERE id = ?", (cur.lastrowid,)).fetchone()
    conn.close()
    return row
