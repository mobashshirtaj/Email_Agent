import imaplib
import email
from email.header import decode_header
import os

with open("app_pass_gmai_emaiBot.txt","r",encoding='utf-8') as file:
    content = file.read()

# 1. Setup credentials
GMAIL_USER = "mobashshir.taj@gmail.com"
APP_PASSWORD = str(content)  # Paste your generated app password here (no spaces)

def decode_mime_header(header_value):
    """Safely decodes email headers like Subject and From."""
    if not header_value:
        return "No Subject/Sender"
        
    try:
        decoded_elements = decode_header(header_value)
        # Safely extract the first element
        first_element = decoded_elements[0]
        
        # Check if the element contains both text and encoding format
        if isinstance(first_element, tuple) and len(first_element) == 2:
            decoded, encoding = first_element
            if isinstance(decoded, bytes):
                return decoded.decode(encoding or "utf-8", errors="ignore")
            return str(decoded)
        elif isinstance(first_element, tuple):
            # Fallback if it's a tuple but missing the encoding parameter
            decoded = first_element[0]
            if isinstance(decoded, bytes):
                return decoded.decode("utf-8", errors="ignore")
            return str(decoded)
        else:
            return str(first_element)
            
    except Exception:
        # Absolute fallback if the header is completely corrupted
        return str(header_value)
    
def extract_email_contents(msg, save_directory="downloaded_images"):
    """
    Extracts the text body and saves images from an email message object.
    """
    print("\n--- EMAIL CONTENTS ---")
    
    # 1. Walk through the parts of the email
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            
            # --- EXTRACT TEXT WRITING ---
            # 'text/plain' gives you the raw text. 'text/html' gives the styled version.
            if content_type == "text/plain" and "attachment" not in content_disposition:
                body = part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8', errors='ignore')
                print("📝 [Text Body]:")
                print(body)
                
            # --- EXTRACT IMAGES ---
            elif "image" in content_type:
                # Get the filename of the image
                filename = part.get_filename()
                if filename:
                    # Create a folder to save images if it doesn't exist
                    if not os.path.exists(save_directory):
                        os.makedirs(save_directory)
                        
                    filepath = os.path.join(save_directory, filename)
                    
                    # Download and save the image file
                    with open(filepath, "wb") as f:
                        f.write(part.get_payload(decode=True))
                    print(f"📷 [Saved Image Attachment]: {filepath}")
                    
    else:
        # If the email is not multipart, it's just a simple plain text email
        body = msg.get_payload(decode=True).decode(msg.get_content_charset() or 'utf-8', errors='ignore')
        print("📝 [Text Body]:")
        print(body)

def print_email_summary(msg):
    """Utility to print sender and subject consistently."""
    subject = decode_mime_header(msg.get("Subject"))
    sender = decode_mime_header(msg.get("From"))
    print(f"  • From: {sender}\n    Subject: {subject}")

try:
    # 1. Initialize and Log In
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(GMAIL_USER, APP_PASSWORD)
    
    # ==========================================
    # BUCKET 1, 2 & 3: PROCESSING THE INBOX
    # ==========================================
    # Open Inbox in read-only mode so we don't accidentally alter unread statuses
    mail.select("INBOX", readonly=True)
    
    print("\n🔍 --- PROCESSING INBOX ---")
    
    # 1. Unread Mails
    _, unseen_data = mail.search(None, "UNSEEN")
    unseen_ids = unseen_data[0].split()
    print(f"\n📥 Unread Emails ({len(unseen_ids)} total) - Showing last 3:")
    for e_id in unseen_ids[-3:]:
        _, msg_data = mail.fetch(e_id, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])
        print_email_summary(msg)
        extract_email_contents(msg)

    # 2. Read but NOT Replied Mails
    # IMAP criteria 'SEEN' combined with 'NOT ANSWERED'
    _, read_not_replied_data = mail.search(None, "SEEN", "NOT", "ANSWERED")
    rnr_ids = read_not_replied_data[0].split()
    print(f"\n👀 Read but NOT Replied ({len(rnr_ids)} total) - Showing last 3:")
    for e_id in rnr_ids[-3:]:
        _, msg_data = mail.fetch(e_id, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])
        print_email_summary(msg)

    # 3. Replied Mails (And tracking down the reply)
    _, replied_data = mail.search(None, "ANSWERED")
    replied_ids = replied_data[0].split()
    print(f"\n💬 Replied Emails ({len(replied_ids)} total) - Showing last 2 with their tracking info:")
    
    for e_id in replied_ids[-2:]:
        _, msg_data = mail.fetch(e_id, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])
        subject = decode_mime_header(msg.get("Subject"))
        msg_id = msg.get("Message-ID")
        
        print(f"  • Original Email Subject: {subject}")
        
        # To find the actual reply text, we switch context to the Sent folder
        # and look for an email referencing this Message-ID
        if msg_id:
            mail.select('"[Gmail]/Sent Mail"', readonly=True)
            # Search for your reply referencing the original message ID
            _, sent_data = mail.search(None, f'HEADER In-Reply-To "{msg_id}"')
            sent_ids = sent_data[0].split()
            
            if sent_ids:
                _, reply_data = mail.fetch(sent_ids[0], "(RFC822)")
                reply_msg = email.message_from_bytes(reply_data[0][1])
                reply_subject = decode_mime_header(reply_msg.get("Subject"))
                print(f"    ↳ Found Reply in Sent folder! Subject: {reply_subject}")
            else:
                print("    ↳ Reply was sent, but could not locate the text block in Sent Mail.")
            
            # Switch back to Inbox for subsequent routines
            mail.select("INBOX", readonly=True)

    # ==========================================
    # BUCKETS 4: PROCESSING THE SPAM FOLDER
    # ==========================================
    print("\n🔍 --- PROCESSING SPAM FOLDER ---")
    # Gmail's system folders require quotes because of the bracket structure
    mail.select('"[Gmail]/Spam"', readonly=True)
    
    _, spam_data = mail.search(None, "ALL")
    spam_ids = spam_data[0].split()
    print(f"\n🚨 Spam Emails ({len(spam_ids)} total) - Showing last 3:")
    for e_id in spam_ids[-3:]:
        _, msg_data = mail.fetch(e_id, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])
        print_email_summary(msg)

    # 5. Clean up connection
    mail.logout()
    print("\nSession Closed Successfully.")

except Exception as e:
    print(f"\nAn error occurred during execution: {e}")

