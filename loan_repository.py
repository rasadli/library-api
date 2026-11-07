import db


def list_loans():
    conn = db.connect()
    rows = conn.execute("SELECT * FROM loans").fetchall()
    conn.close()
    return rows


def list_loans_for_member(member_id):
    conn = db.connect()
    rows = conn.execute("SELECT * FROM loans WHERE member_id = ?", (member_id,)).fetchall()
    conn.close()
    return rows


def get_loan(loan_id):
    conn = db.connect()
    row = conn.execute("SELECT * FROM loans WHERE id = ?", (loan_id,)).fetchone()
    conn.close()
    return row


def create_loan(book_id, member_id, due_date, checked_out):
    conn = db.connect()
    cur = conn.execute("INSERT INTO loans (book_id, member_id, due_date, checked_out) VALUES (?, ?, ?, ?)", (book_id, member_id, due_date, checked_out))
    conn.execute("UPDATE books SET available = 0 WHERE id = ?", (book_id,))
    conn.commit()
    row = conn.execute("SELECT * FROM loans WHERE id = ?", (cur.lastrowid,)).fetchone()
    conn.close()
    return row


def mark_returned(loan_id, book_id, fine):
    conn = db.connect()
    conn.execute("UPDATE loans SET returned = 1, fine = ? WHERE id = ?", (fine, loan_id))
    conn.execute("UPDATE books SET available = 1 WHERE id = ?", (book_id,))
    conn.commit()
    row = conn.execute("SELECT * FROM loans WHERE id = ?", (loan_id,)).fetchone()
    conn.close()
    return row


def extend_loan(loan_id, new_due_date):
    conn = db.connect()
    conn.execute("UPDATE loans SET due_date = ?, renewals = renewals + 1 WHERE id = ?", (new_due_date, loan_id))
    conn.commit()
    row = conn.execute("SELECT * FROM loans WHERE id = ?", (loan_id,)).fetchone()
    conn.close()
    return row


def mark_fine_paid(loan_id):
    conn = db.connect()
    conn.execute("UPDATE loans SET fine_paid = 1 WHERE id = ?", (loan_id,))
    conn.commit()
    row = conn.execute("SELECT * FROM loans WHERE id = ?", (loan_id,)).fetchone()
    conn.close()
    return row
