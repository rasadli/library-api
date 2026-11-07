from datetime import date, timedelta

import book_repository
import fines
import loan_repository
import member_repository
import notifications
import validation
from errors import bad_request, conflict, not_found

STUDENT_LOAN_LIMIT = 3
STAFF_LOAN_LIMIT = 5
LOAN_DAYS = 14


def amount_owed(loan):
    if not loan["returned"]:
        return fines.fine_for(loan["due_date"])
    if not loan["fine_paid"]:
        return loan["fine"]
    return 0


def total_owed(loans):
    return sum(amount_owed(loan) for loan in loans)


def count_open_loans(loans):
    return sum(1 for loan in loans if not loan["returned"])


def current_fine(loan):
    return fines.fine_for(loan["due_date"]) if not loan["returned"] else loan["fine"]


def is_overdue(loan):
    return not loan["returned"] and fines.days_late(loan["due_date"]) > 0


def loan_json(loan, include_current_fine=False):
    result = {
        "id": loan["id"], "book_id": loan["book_id"],
        "member_id": loan["member_id"], "due_date": loan["due_date"],
        "returned": bool(loan["returned"]), "fine": fines.money(loan["fine"]),
        "fine_paid": bool(loan["fine_paid"]), "renewals": loan["renewals"],
        "checked_out": loan["checked_out"],
    }
    if include_current_fine:
        result["current_fine"] = fines.money(current_fine(loan))
    return result


def list_loans(only_overdue):
    rows = loan_repository.list_loans()
    return [loan_json(loan, True) for loan in rows if not only_overdue or is_overdue(loan)]


def get_loan(loan_id):
    loan = loan_repository.get_loan(loan_id)
    if loan is None:
        raise not_found("loan not found")
    return loan_json(loan, True)


def create_loan(data):
    if not data.get("book_id") or not data.get("member_id"):
        raise bad_request("book_id and member_id are required")
    if data.get("due_date") and not validation.is_valid_date(data["due_date"]):
        raise bad_request("invalid due_date")
    book = book_repository.get_book(data["book_id"])
    if book is None:
        raise not_found("book not found")
    member = member_repository.get_member(data["member_id"])
    if member is None:
        raise not_found("member not found")
    if book["available"] == 0:
        raise conflict("book is not available")
    loans = loan_repository.list_loans_for_member(data["member_id"])
    if total_owed(loans) > 0:
        raise conflict("member has unpaid fines")
    limit = STAFF_LOAN_LIMIT if member["type"] == "staff" else STUDENT_LOAN_LIMIT
    if count_open_loans(loans) >= limit:
        raise conflict("loan limit reached")
    today = date.today()
    due = data.get("due_date") or (today + timedelta(days=LOAN_DAYS)).isoformat()
    loan = loan_repository.create_loan(data["book_id"], data["member_id"], due, today.isoformat())
    notifications.send_email(member["email"], "Book checked out", "You checked out " + book["title"])
    return loan_json(loan)


def return_book(loan_id):
    loan = loan_repository.get_loan(loan_id)
    if loan is None:
        raise not_found("loan not found")
    if loan["returned"]:
        raise conflict("loan already returned")
    fine = fines.fine_for(loan["due_date"])
    updated = loan_repository.mark_returned(loan_id, loan["book_id"], fine)
    member = member_repository.get_member(loan["member_id"])
    book = book_repository.get_book(loan["book_id"])
    notifications.send_email(member["email"], "Book returned", "You returned " + book["title"] + ". Fine: $" + str(fines.money(fine)))
    return loan_json(updated)


def renew_loan(loan_id):
    loan = loan_repository.get_loan(loan_id)
    if loan is None:
        raise not_found("loan not found")
    if loan["returned"]:
        raise conflict("loan already returned")
    if date.fromisoformat(loan["due_date"]) < date.today():
        raise conflict("overdue loans cannot be renewed")
    if loan["renewals"] >= 1:
        raise conflict("loan was already renewed")
    new_due = (date.fromisoformat(loan["due_date"]) + timedelta(days=LOAN_DAYS)).isoformat()
    updated = loan_repository.extend_loan(loan_id, new_due)
    member = member_repository.get_member(loan["member_id"])
    book = book_repository.get_book(loan["book_id"])
    notifications.send_email(member["email"], "Loan renewed", "You renewed " + book["title"])
    return loan_json(updated)


def pay_fine(loan_id):
    loan = loan_repository.get_loan(loan_id)
    if loan is None:
        raise not_found("loan not found")
    if not loan["returned"]:
        raise conflict("return the book before paying")
    if loan["fine"] <= 0 or loan["fine_paid"]:
        raise conflict("no fine to pay")
    updated = loan_repository.mark_fine_paid(loan_id)
    member = member_repository.get_member(loan["member_id"])
    notifications.send_email(member["email"], "Fine paid", "We received $" + str(fines.money(loan["fine"])))
    return loan_json(updated)
