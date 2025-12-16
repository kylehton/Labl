import mailbox
import json
import os
from bs4 import BeautifulSoup
import re
import hashlib

def make_local_id(msg):
    key = (
        (msg.get("Message-ID") or "") +
        (msg.get("Date") or "") +
        (msg.get("From") or "") +
        (msg.get("Subject") or "")
    )
    return hashlib.sha256(key.encode("utf-8", errors="ignore")).hexdigest()

def html_to_text(html_bytes):
    soup = BeautifulSoup(html_bytes, "lxml")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator=" ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# Folder containing all your MBOX files
mbox_folder = "inbox"
output_file = "emails.jsonl"

# Get all .mbox files in the folder
mbox_files = [os.path.join(mbox_folder, f) for f in os.listdir(mbox_folder) if f.endswith(".mbox")]

with open(output_file, "w", encoding="utf-8") as out_f:
    for mbox_file in mbox_files:
        print(f"Processing {mbox_file}...")
        mbox = mailbox.mbox(mbox_file)

        for message in mbox:
            email_data = {
                "from": message["From"],
                "subject": message["Subject"],
                "date": message["Date"],
                "local_id": make_local_id(message),
                "mail_id": message["Message-ID"],
                "body": ""
            }

            # Extract body
            plain_text = None
            html_text = None

            if message.is_multipart():
                for part in message.walk():
                    if part.is_multipart():
                        continue

                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition", ""))

                    if "attachment" in content_disposition:
                        continue

                    payload = part.get_payload(decode=True)
                    if not payload:
                        continue

                    if content_type == "text/plain" and plain_text is None:
                        plain_text = payload.decode(errors="ignore")

                    elif content_type == "text/html" and html_text is None:
                        html_text = payload
            else:
                payload = message.get_payload(decode=True)
                content_type = message.get_content_type()

                if payload:
                    if content_type == "text/plain":
                        plain_text = payload.decode(errors="ignore")
                    elif content_type == "text/html":
                        html_text = payload

            if plain_text and plain_text.strip():
                email_data["body"] = plain_text
            elif html_text:
                email_data["body"] = html_to_text(html_text)
            else:
                email_data["body"] = ""


            email_data["body"] = re.sub(r"\s+", " ", email_data["body"]).strip()

            # Write each email as a separate JSON line
            out_f.write(json.dumps(email_data, ensure_ascii=False) + "\n")

    print(f"All emails processed into {output_file}")
