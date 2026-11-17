import checks
import member_repository
import loan_repository
import loan_service
import fines
import validation
from errors import bad_request, conflict


def list_members():
    return member_repository.list_members()


def get_member(member_id):
    return checks.require_member(member_id)


def create_member(data):
    if not data.get("name"):
        raise bad_request("name is required")
    if not validation.is_valid_email(data.get("email")):
        raise bad_request("invalid email")
    member_type = data.get("type", "student")
    if not validation.is_valid_member_type(member_type):
        raise bad_request("type must be student or staff")
    if member_repository.get_member_by_email(data["email"]) is not None:
        raise conflict("email already registered")
    return member_repository.create_member(data["name"], data["email"], member_type)


def member_account(member_id):
    member = get_member(member_id)
    rows = loan_repository.list_loans_for_member(member_id)
    loans = [{
        "id": loan["id"], "book_id": loan["book_id"],
        "due_date": loan["due_date"], "returned": bool(loan["returned"]),
        "fine": fines.money(loan["fine"]), "fine_paid": bool(loan["fine_paid"]),
    } for loan in rows]
    limit = checks.loan_limit_for(member)
    return {"loans": loans, "total_owed": fines.money(loan_service.total_owed(rows)),
            "loans_remaining": limit - loan_service.count_open_loans(rows)}
