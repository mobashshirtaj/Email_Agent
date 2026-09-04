from pathlib import Path

from email_utils import (
    load_emails_from_pdf,
    save_emails_to_json
)


DATA_DIR = Path("data/output")


FILES = [
    {
        "pdf": "unread_emails.pdf",
        "json": "unread_emails.json",
        "source": "unread"
    },
    {
        "pdf": "read_and_replied_emails.pdf",
        "json": "read_and_replied_emails.json",
        "source": "read_and_replied"
    },
    {
        "pdf": "read_not_replied_emails.pdf",
        "json": "read_emails.json",
        "source": "read"
    }
]


def process_pdf(file_info):

    pdf_path = DATA_DIR / file_info["pdf"]
    json_path = DATA_DIR / file_info["json"]

    print("\n" + "=" * 60)
    print(f"Processing: {pdf_path.name}")
    print("=" * 60)

    emails = load_emails_from_pdf(
        str(pdf_path),
        file_info["source"]
    )

    print(f"Emails extracted: {len(emails)}")

    save_emails_to_json(
        emails,
        str(json_path)
    )

    print(f"Saved: {json_path}")

    if emails:

        print("\nFirst email:")

        email = emails[0]

        print(f"From: {email['sender']}")
        print(f"Subject: {email['subject']}")
        print(f"Date: {email['date']}")
        print(f"Source: {email['source']}")
        print(f"Body:\n{email['body'][:500]}")


def main():

    print("=" * 60)
    print("EMAIL DATASET BUILDER")
    print("=" * 60)

    for file_info in FILES:

        process_pdf(file_info)

    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)


if __name__ == "__main__":
    main()