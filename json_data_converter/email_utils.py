import re
import json
from typing import TypedDict

from pypdf import PdfReader


class Reply(TypedDict):
    sender: str
    subject: str
    date: str
    body: str


class Email(TypedDict):
    sender: str
    subject: str
    date: str
    body: str
    source: str


class RepliedEmail(TypedDict):
    sender: str
    subject: str
    date: str
    body: str
    reply: Reply
    source: str


def extract_pdf_text(pdf_path: str) -> str:
    """
    Extract text from every page of the PDF.
    """

    reader = PdfReader(pdf_path)

    pages = []

    for page in reader.pages:

        text = page.extract_text()

        if text:
            pages.append(text)

    return "\n".join(pages)


def clean_text(text: str) -> str:
    """
    Basic text cleanup.
    """

    if not text:
        return ""

    # Remove excessive spaces/tabs
    text = re.sub(r"[ \t]+", " ", text)

    # Remove excessive blank lines
    text = re.sub(r"\n\s*\n+", "\n\n", text)

    return text.strip()


def extract_email_fields(block: str):
    """
    Extract From, Subject, Date and Content
    from one email section.
    """

    from_match = re.search(
        r"From:\s*(.*?)(?=\nSubject:)",
        block,
        re.DOTALL
    )

    subject_match = re.search(
        r"Subject:\s*(.*?)(?=\nDate:)",
        block,
        re.DOTALL
    )

    date_match = re.search(
        r"Date:\s*(.*?)(?=\nContent:)",
        block,
        re.DOTALL
    )

    content_match = re.search(
        r"Content:\s*(.*?)(?=\Z)",
        block,
        re.DOTALL
    )

    if not from_match:
        return None

    return {
        "sender": clean_text(from_match.group(1)),
        "subject": clean_text(
            subject_match.group(1)
        ) if subject_match else "",
        "date": clean_text(
            date_match.group(1)
        ) if date_match else "",
        "body": clean_text(
            content_match.group(1)
        ) if content_match else ""
    }


def remove_quoted_reply(body: str) -> str:
    """
    Remove the previous email quoted underneath
    the user's actual reply.
    """

    patterns = [
        r"\nOn .*?wrote:\s*",
        r"\nOn .*? wrote:\s*",
        r"\nFrom: .*?\nSent: .*?\n",
        r"\n> .*"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            body,
            re.DOTALL | re.IGNORECASE
        )

        if match:
            body = body[:match.start()]

    return clean_text(body)


def parse_replied_email_block(block: str):
    """
    Parse one EMAIL + MY REPLY block.
    """

    parts = re.split(
        r"(?m)^\s*MY REPLY\s*$",
        block,
        maxsplit=1
    )

    if len(parts) != 2:
        return None

    original_section = parts[0]
    reply_section = parts[1]

    original = extract_email_fields(
        original_section
    )

    reply = extract_email_fields(
        reply_section
    )

    if not original or not reply:
        return None

    reply["body"] = remove_quoted_reply(
        reply["body"]
    )

    return {
        "sender": original["sender"],
        "subject": original["subject"],
        "date": original["date"],
        "body": original["body"],
        "reply": reply,
        "source": "read_and_replied"
    }


def parse_replied_emails(text: str):
    """
    Parse the complete read-and-replied PDF.
    """

    blocks = re.split(
        r"(?m)^\s*EMAIL\s*$",
        text
    )

    emails = []

    for block in blocks:

        email = parse_replied_email_block(
            block
        )

        if email:
            emails.append(email)

    return emails


def parse_normal_email_block(
    block: str,
    source: str
):
    """
    Parse a normal email without a reply.
    """

    email = extract_email_fields(block)

    if not email:
        return None

    return {
        "sender": email["sender"],
        "subject": email["subject"],
        "date": email["date"],
        "body": email["body"],
        "source": source
    }


def parse_normal_emails(
    text: str,
    source: str
):
    """
    Parse unread/read-only emails.
    """

    blocks = re.split(
        r"(?m)^\s*EMAIL\s*$",
        text
    )

    emails = []

    for block in blocks:

        email = parse_normal_email_block(
            block,
            source
        )

        if email:
            emails.append(email)

    return emails


def load_emails_from_pdf(
    pdf_path: str,
    source: str
):
    """
    Load and parse a PDF according to its source.
    """

    text = extract_pdf_text(pdf_path)

    if source == "read_and_replied":

        return parse_replied_emails(text)

    return parse_normal_emails(
        text,
        source
    )


def save_emails_to_json(
    emails,
    output_path: str
):
    """
    Save emails as JSON.
    """

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            emails,
            f,
            indent=2,
            ensure_ascii=False
        )