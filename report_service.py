import book_repository
import fines
import loan_repository
import loan_service
import report_repository


def overdue_report():
    items = []
    total = 0
    for row in report_repository.list_open_loans_with_details():
        days = fines.days_late(row["due_date"])
        if days > 0:
            fine = fines.fine_for(row["due_date"])
            total += fine
            items.append({"loan_id": row["id"], "title": row["title"], "member": row["name"],
                          "days_late": days, "fine": fines.money(fine)})
    return {"items": items, "total_fines": fines.money(total)}


def summary_report():
    loans = loan_repository.list_loans()
    return {"total_books": book_repository.count_books(),
            "on_loan": loan_service.count_open_loans(loans),
            "fines_outstanding": fines.money(loan_service.total_owed(loans))}
