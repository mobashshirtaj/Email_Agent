import os

from config import OUTPUT_DIRECTORY
from email_utils import (
    get_emails_by_search
)

from pdf_generator import PDFWriter


def process_emails_with_images():

    print(
        "\n========================================"
    )

    print(
        "Processing emails with images..."
    )

    print(
        "========================================"
    )


    output_file = os.path.join(
        OUTPUT_DIRECTORY,
        "emails_with_images.pdf"
    )


    writer = PDFWriter(
        output_file,
        "Emails With Images",
        include_images=True
    )


    processed = 0
    matched = 0


    try:

        for (
            emails,
            start,
            end,
            total
        ) in get_emails_by_search(
            "INBOX",
            ("ALL",),
            download_images=True
        ):

            for email_data in emails:

                processed += 1


                if email_data.get(
                    "images"
                ):

                    matched += 1

                    writer.add_email(
                        email_data
                    )


            print(
                f"Image scan: "
                f"{min(end, total):,}/{total:,} "
                f"| Found: {matched:,}"
            )


        writer.close()


    except Exception:

        print(
            "\nImage processing failed."
        )

        raise


    print(
        f"Finished image scan."
    )

    print(
        f"Emails containing images: "
        f"{matched:,}"
    )