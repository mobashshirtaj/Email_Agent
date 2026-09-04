import os

from config import OUTPUT_DIRECTORY
from email_utils import (
    connect_to_gmail,
    search_uids,
    email_batch_generator,
)

from pdf_generator import PDFWriter


# ============================================================
# Normalize Message ID
# ============================================================

def normalize_message_id(value):

    if not value:
        return ""

    value = value.strip()

    # Remove surrounding < >
    value = value.strip("<>")

    return value.lower()


# ============================================================
# Build Sent Reply Map
# ============================================================

def build_sent_reply_map():

    print(
        "\nScanning Sent Mail for replies..."
    )

    reply_map = {}


    # --------------------------------------------------------
    # Get Sent Mail UIDs
    # --------------------------------------------------------

    mail = connect_to_gmail()

    try:

        sent_uids = search_uids(
            mail,
            '"[Gmail]/Sent Mail"',
            "ALL"
        )

    finally:

        try:
            mail.logout()
        except Exception:
            pass


    print(
        f"Found {len(sent_uids):,} sent emails."
    )


    # --------------------------------------------------------
    # Fetch Sent Mail in batches
    # --------------------------------------------------------

    for (
        emails,
        start,
        end,
        total
    ) in email_batch_generator(
        '"[Gmail]/Sent Mail"',
        sent_uids,
        download_images=False
    ):

        for sent_email in emails:

            in_reply_to = normalize_message_id(
                sent_email.get(
                    "in_reply_to",
                    ""
                )
            )


            if in_reply_to:

                reply_map[
                    in_reply_to
                ] = sent_email


            # ------------------------------------------------
            # Also use References
            #
            # Some email clients don't populate
            # In-Reply-To consistently.
            # ------------------------------------------------

            references = sent_email.get(
                "references",
                ""
            )

            if references:

                reference_ids = (
                    references.split()
                )

                for reference_id in reference_ids:

                    normalized = (
                        normalize_message_id(
                            reference_id
                        )
                    )

                    if normalized:

                        reply_map[
                            normalized
                        ] = sent_email


        print(
            f"Sent Mail scanned: "
            f"{min(end, total):,}/{total:,}"
        )


    print(
        f"Reply relationships found: "
        f"{len(reply_map):,}"
    )


    return reply_map


# ============================================================
# Process Replied Emails
# ============================================================

def process_replied_emails():

    print(
        "\n========================================"
    )

    print(
        "Processing read and replied emails..."
    )

    print(
        "========================================"
    )


    output_file = os.path.join(
        OUTPUT_DIRECTORY,
        "read_and_replied_emails.pdf"
    )


    # --------------------------------------------------------
    # Build Sent Mail mapping first
    # --------------------------------------------------------

    reply_map = (
        build_sent_reply_map()
    )


    # --------------------------------------------------------
    # Create PDF
    # --------------------------------------------------------

    writer = PDFWriter(
        output_file,
        "Read and Replied Emails",
        include_replies=True
    )


    processed = 0
    matched = 0


    try:

        # ----------------------------------------------------
        # Search answered Inbox emails
        # ----------------------------------------------------

        mail = connect_to_gmail()

        try:

            inbox_uids = search_uids(
                mail,
                "INBOX",
                "ANSWERED"
            )

        finally:

            try:
                mail.logout()
            except Exception:
                pass


        print(
            f"Found {len(inbox_uids):,} "
            f"replied Inbox emails."
        )


        # ----------------------------------------------------
        # Process Inbox in batches
        # ----------------------------------------------------

        for (
            emails,
            start,
            end,
            total
        ) in email_batch_generator(
            "INBOX",
            inbox_uids,
            download_images=False
        ):

            for email_data in emails:

                processed += 1


                # --------------------------------------------
                # Match original email Message-ID
                # --------------------------------------------

                message_id = (
                    normalize_message_id(
                        email_data.get(
                            "message_id",
                            ""
                        )
                    )
                )


                reply = reply_map.get(
                    message_id
                )


                # --------------------------------------------
                # Attach reply
                # --------------------------------------------

                if reply:

                    email_data[
                        "reply"
                    ] = reply

                    matched += 1


                else:

                    email_data[
                        "reply"
                    ] = None


                writer.add_email(
                    email_data
                )


            print(
                f"Read & replied: "
                f"{min(end, total):,}/{total:,} "
                f"| Replies matched: {matched:,}"
            )


        writer.close()


    except Exception:

        print(
            "\nRead and replied processing failed."
        )

        raise


    print(
        f"\nFinished."
    )

    print(
        f"Incoming replied emails: "
        f"{processed:,}"
    )

    print(
        f"Actual sent replies matched: "
        f"{matched:,}"
    )