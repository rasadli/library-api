import book_repository
import loan_repository
import member_repository
from config import STAFF_LOAN_LIMIT, STUDENT_LOAN_LIMIT
from errors import conflict, not_found


def require_book(book_id):
    book = book_repository.get_book(book_id)
    if book is None:
        raise not_found("book not found")
    return book


def require_member(member_id):
    member = member_repository.get_member(member_id)
    if member is None:
        raise not_found("member not found")
    return member


def require_loan(loan_id):
    loan = loan_repository.get_loan(loan_id)
    if loan is None:
        raise not_found("loan not found")
    return loan


def require_book_available(book):
    if book["available"] == 0:
        raise conflict("book is not available")


def require_book_not_on_loan(book):
    if book["available"] == 0:
        raise conflict("book is on loan")


def loan_limit_for(member):
    return STAFF_LOAN_LIMIT if member["type"] == "staff" else STUDENT_LOAN_LIMIT


def require_can_borrow(member, open_loans, amount_owed):
    if amount_owed > 0:
        raise conflict("member has unpaid fines")
    if open_loans >= loan_limit_for(member):
        raise conflict("loan limit reached")
