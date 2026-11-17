OUTBOX_PATH = "outbox.txt"


class MockEmailSender:
    """Mock object: stands in for a real mail server.
    It records every message in `sent` and writes it to outbox.txt instead of sending email."""

    def __init__(self, outbox_path=OUTBOX_PATH):
        self.outbox_path = outbox_path
        self.sent = []

    def send_email(self, email, subject, body):
        self.sent.append({"to": email, "subject": subject, "body": body})
        with open(self.outbox_path, "a") as f:
            f.write("TO: " + email + " | SUBJECT: " + subject + " | BODY: " + body + "\n")


sender = MockEmailSender()


def send_email(email, subject, body):
    sender.send_email(email, subject, body)
