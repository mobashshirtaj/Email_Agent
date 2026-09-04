import os
import re
import html
import email
import imaplib

from email import policy
from email.header import decode_header
from bs4 import BeautifulSoup

from config import (
    GMAIL_USER,
    APP_PASSWORD,
    IMAP_SERVER,
    IMAP_PORT,
    IMAP_TIMEOUT,
    IMAGE_DIRECTORY,
    BATCH_SIZE,
)


# ============================================================
# Gmail Connection
# ============================================================

def connect_to_gmail():

    mail = imaplib.IMAP4_SSL(
        IMAP_SERVER,
        IMAP_PORT,
        timeout=IMAP_TIMEOUT
    )

    mail.login(
        GMAIL_USER,
        APP_PASSWORD
    )

    return mail


# ============================================================
# Select Mailbox
# ============================================================

def select_mailbox(mail, mailbox):

    status, data = mail.select(
        mailbox,
        readonly=True
    )

    if status != "OK":

        raise RuntimeError(
            f"Could not select mailbox: {mailbox}"
        )

    return data


# ============================================================
# Decode MIME Header
# ============================================================

def decode_mime_header(value):

    if not value:
        return ""

    decoded_parts = []

    try:

        for part, encoding in decode_header(value):

            if isinstance(part, bytes):

                try:

                    part = part.decode(
                        encoding or "utf-8",
                        errors="replace"
                    )

                except Exception:

                    part = part.decode(
                        "utf-8",
                        errors="replace"
                    )

            decoded_parts.append(
                str(part)
            )

    except Exception:

        return str(value)

    return "".join(
        decoded_parts
    )


# ============================================================
# Clean Email Body
# ============================================================

def clean_email_body(text):

    if not text:
        return "No readable content found."


    # --------------------------------------------------------
    # Remove null bytes
    # --------------------------------------------------------

    text = text.replace(
        "\x00",
        ""
    )


    # --------------------------------------------------------
    # Decode HTML entities
    #
    # &nbsp;
    # &amp;
    # &lt;
    # etc.
    # --------------------------------------------------------

    text = html.unescape(
        text
    )


    # --------------------------------------------------------
    # Detect HTML
    # --------------------------------------------------------

    if (
        "<html" in text.lower()
        or "<body" in text.lower()
        or "<div" in text.lower()
        or "<p>" in text.lower()
        or "<br" in text.lower()
        or "<table" in text.lower()
    ):

        try:

            soup = BeautifulSoup(
                text,
                "html.parser"
            )

            # Remove elements that should never
            # appear in readable email content.

            for tag in soup(
                [
                    "script",
                    "style",
                    "head",
                    "meta",
                    "link",
                    "noscript"
                ]
            ):

                tag.decompose()

            text = soup.get_text(
                separator="\n"
            )

        except Exception:

            # Fallback if HTML parser fails
            text = re.sub(
                r"<[^>]+>",
                " ",
                text
            )


    # --------------------------------------------------------
    # Remove remaining HTML tags
    # --------------------------------------------------------

    text = re.sub(
        r"<[^>]+>",
        " ",
        text
    )


    # --------------------------------------------------------
    # Remove common HTML/CSS artifacts
    # --------------------------------------------------------

    text = re.sub(
        r"\b(?:font-family|font-size|line-height|"
        r"background-color|margin|padding)\s*:[^;]+;?",
        " ",
        text,
        flags=re.IGNORECASE
    )


    # --------------------------------------------------------
    # Remove excessive whitespace
    # --------------------------------------------------------

    lines = []

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        # Remove extremely long garbage lines
        # such as encoded/CSS data.
        if len(line) > 5000:
            continue

        lines.append(
            line
        )


    text = "\n".join(
        lines
    )


    # --------------------------------------------------------
    # Remove excessive blank lines
    # --------------------------------------------------------

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )


    # --------------------------------------------------------
    # Remove excessive spaces
    # --------------------------------------------------------

    text = re.sub(
        r"[ \t]{2,}",
        " ",
        text
    )


    text = text.strip()


    if not text:

        return "No readable content found."


    return text


# ============================================================
# Safe Filename
# ============================================================

def safe_filename(filename):

    if not filename:

        return "image"

    filename = decode_mime_header(
        filename
    )

    invalid_chars = '<>:"/\\|?*'

    for char in invalid_chars:

        filename = filename.replace(
            char,
            "_"
        )

    return filename[:200]


# ============================================================
# Extract Email Data
# ============================================================

def extract_email_data(
    msg,
    download_images=False
):

    subject = decode_mime_header(
        msg.get(
            "Subject",
            ""
        )
    )

    sender = decode_mime_header(
        msg.get(
            "From",
            ""
        )
    )

    date = decode_mime_header(
        msg.get(
            "Date",
            ""
        )
    )

    message_id = msg.get(
        "Message-ID",
        ""
    ).strip()

    in_reply_to = msg.get(
        "In-Reply-To",
        ""
    ).strip()

    references = msg.get(
        "References",
        ""
    ).strip()


    body_plain = []
    body_html = []

    images = []


    # ========================================================
    # Walk MIME parts
    # ========================================================

    for part in msg.walk():

        content_type = (
            part.get_content_type()
        )

        disposition = str(
            part.get(
                "Content-Disposition",
                ""
            )
        ).lower()


        # ----------------------------------------------------
        # Plain text
        # ----------------------------------------------------

        if content_type == "text/plain":

            try:

                payload = part.get_payload(
                    decode=True
                )

                if payload:

                    charset = (
                        part.get_content_charset()
                        or "utf-8"
                    )

                    text = payload.decode(
                        charset,
                        errors="replace"
                    )

                    body_plain.append(
                        text
                    )

            except Exception:

                pass


        # ----------------------------------------------------
        # HTML
        # ----------------------------------------------------

        elif content_type == "text/html":

            try:

                payload = part.get_payload(
                    decode=True
                )

                if payload:

                    charset = (
                        part.get_content_charset()
                        or "utf-8"
                    )

                    text = payload.decode(
                        charset,
                        errors="replace"
                    )

                    body_html.append(
                        text
                    )

            except Exception:

                pass


        # ----------------------------------------------------
        # Images
        # ----------------------------------------------------

        elif content_type.startswith(
            "image/"
        ):

            filename = part.get_filename()

            if not filename:

                extension = (
                    content_type.split("/")[-1]
                )

                filename = (
                    f"image.{extension}"
                )

            filename = safe_filename(
                filename
            )


            if download_images:

                try:

                    image_data = (
                        part.get_payload(
                            decode=True
                        )
                    )

                    if image_data:

                        base, extension = (
                            os.path.splitext(
                                filename
                            )
                        )

                        image_path = os.path.join(
                            IMAGE_DIRECTORY,
                            filename
                        )

                        counter = 1

                        while os.path.exists(
                            image_path
                        ):

                            image_path = os.path.join(
                                IMAGE_DIRECTORY,
                                f"{base}_{counter}{extension}"
                            )

                            counter += 1

                        with open(
                            image_path,
                            "wb"
                        ) as image_file:

                            image_file.write(
                                image_data
                            )

                        images.append(
                            image_path
                        )

                except Exception:

                    pass

            else:

                images.append(
                    filename
                )


    # ========================================================
    # Choose body
    #
    # Plain text is preferred.
    # HTML is fallback.
    # ========================================================

    if body_plain:

        body = "\n\n".join(
            body_plain
        )

    elif body_html:

        body = "\n\n".join(
            body_html
        )

    else:

        body = "No readable content found."


    # ========================================================
    # Clean body
    # ========================================================

    body = clean_email_body(
        body
    )


    return {
        "subject": subject,
        "sender": sender,
        "date": date,
        "body": body,

        # Used internally for reply matching
        "message_id": message_id,
        "in_reply_to": in_reply_to,
        "references": references,

        # Used for image PDF
        "images": images,
    }


# ============================================================
# Parse Email
# ============================================================

def parse_email(
    raw_email,
    download_images=False
):

    msg = email.message_from_bytes(
        raw_email,
        policy=policy.default
    )

    return extract_email_data(
        msg,
        download_images=download_images
    )


# ============================================================
# Extract Raw Messages
# ============================================================

def extract_raw_messages(
    fetch_data
):

    messages = []

    for item in fetch_data:

        if not isinstance(
            item,
            tuple
        ):

            continue

        if len(item) < 2:

            continue

        raw_email = item[1]

        if isinstance(
            raw_email,
            bytes
        ):

            messages.append(
                raw_email
            )

    return messages


# ============================================================
# Search UIDs
# ============================================================

def search_uids(
    mail,
    mailbox,
    *criteria
):

    select_mailbox(
        mail,
        mailbox
    )

    status, data = mail.uid(
        "search",
        None,
        *criteria
    )

    if status != "OK":

        raise RuntimeError(
            f"IMAP search failed: "
            f"{criteria}"
        )

    if not data or not data[0]:

        return []

    return data[0].split()


# ============================================================
# Fetch Batch
# ============================================================

def fetch_batch(
    mail,
    mailbox,
    uid_batch,
    download_images=False
):

    if not uid_batch:

        return []


    select_mailbox(
        mail,
        mailbox
    )


    uid_set = b",".join(
        uid_batch
    )


    status, data = mail.uid(
        "fetch",
        uid_set,
        "(BODY.PEEK[])"
    )


    if status != "OK":

        raise ConnectionError(
            "Gmail FETCH failed."
        )


    raw_messages = (
        extract_raw_messages(
            data
        )
    )


    emails = []

    for raw_email in raw_messages:

        try:

            email_data = parse_email(
                raw_email,
                download_images=download_images
            )

            emails.append(
                email_data
            )

        except Exception as exc:

            print(
                f"Warning: Could not parse "
                f"email: {exc}"
            )


    return emails


# ============================================================
# Batch Generator
# ============================================================

def email_batch_generator(
    mailbox,
    uids,
    batch_size=BATCH_SIZE,
    download_images=False
):

    total = len(uids)


    for start in range(
        0,
        total,
        batch_size
    ):

        end = min(
            start + batch_size,
            total
        )

        current_batch = uids[
            start:end
        ]


        attempt = 1


        while attempt <= 3:

            mail = None

            try:

                mail = connect_to_gmail()

                select_mailbox(
                    mail,
                    mailbox
                )

                emails = fetch_batch(
                    mail,
                    mailbox,
                    current_batch,
                    download_images=download_images
                )


                try:

                    mail.logout()

                except Exception:

                    pass


                yield (
                    emails,
                    start,
                    end,
                    total
                )

                break


            except (
                imaplib.IMAP4.abort,
                imaplib.IMAP4.error,
                ConnectionError,
                TimeoutError,
                OSError
            ) as exc:

                print(
                    f"\nIMAP connection error "
                    f"(attempt {attempt}/3): "
                    f"{exc}"
                )


                if mail:

                    try:
                        mail.logout()
                    except Exception:
                        pass


                attempt += 1


                if attempt <= 3:

                    print(
                        "Reconnecting to Gmail..."
                    )


        else:

            raise RuntimeError(
                f"Failed to fetch batch "
                f"{start + 1}-{end} "
                f"after 3 attempts."
            )


# ============================================================
# Search + Batch Processing
# ============================================================

def get_emails_by_search(
    mailbox,
    criteria,
    download_images=False
):

    mail = None

    try:

        mail = connect_to_gmail()

        uids = search_uids(
            mail,
            mailbox,
            *criteria
        )

        print(
            f"Found {len(uids):,} emails."
        )


        try:

            mail.logout()

        except Exception:

            pass


    except Exception:

        if mail:

            try:
                mail.logout()
            except Exception:
                pass

        raise


    yield from email_batch_generator(
        mailbox,
        uids,
        batch_size=BATCH_SIZE,
        download_images=download_images
    )