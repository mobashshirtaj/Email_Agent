import os

from config import OUTPUT_DIRECTORY
from email_utils import get_emails_by_search
from pdf_generator import PDFWriter


def process_unread_emails():

    print(
        "\n========================================"
    )

    print(
        "Processing unread emails..."
    )

    print(
        "========================================"
    )

    output_file = os.path.join(
        OUTPUT_DIRECTORY,
        "unread_emails.pdf"
    )

    writer = PDFWriter(
        output_file,
        "Unread Emails"
    )

    processed = 0

    try:

        for (
            emails,
            start,
            end,
            total
        ) in get_emails_by_search(
            "INBOX",
            ("UNSEEN",),
            download_images=False
        ):

            for email_data in emails:

                writer.add_email(
                    email_data
                )

            processed += len(emails)

            print(
                f"Unread emails: "
                f"{min(end, total):,}/{total:,}"
            )

        # Only close successfully
        writer.close()

        print(
            f"Finished unread emails: "
            f"{processed:,}"
        )

    except Exception:

        print(
            "\nUnread email processing failed."
        )

        raise