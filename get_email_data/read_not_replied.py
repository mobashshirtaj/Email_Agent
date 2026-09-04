import os

from config import OUTPUT_DIRECTORY
from email_utils import get_emails_by_search
from pdf_generator import PDFWriter


def process_read_not_replied():

    print(
        "\n========================================"
    )

    print(
        "Processing read but not replied emails..."
    )

    print(
        "========================================"
    )

    output_file = os.path.join(
        OUTPUT_DIRECTORY,
        "read_not_replied_emails.pdf"
    )

    writer = PDFWriter(
        output_file,
        "Read But Not Replied Emails"
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
            (
                "SEEN",
                "NOT",
                "ANSWERED"
            ),
            download_images=False
        ):

            for email_data in emails:

                writer.add_email(
                    email_data
                )

            processed += len(emails)

            print(
                f"Read/not replied: "
                f"{min(end, total):,}/{total:,}"
            )

        writer.close()

        print(
            f"Finished read/not replied: "
            f"{processed:,}"
        )

    except Exception:

        print(
            "\nRead/not replied processing failed."
        )

        raise