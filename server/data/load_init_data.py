import mailbox
import json
import os

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
                "id": message["Message-ID"],
                "body": ""
            }

            # Extract body
            if message.is_multipart():
                for part in message.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    if content_type == "text/plain" and "attachment" not in content_disposition:
                        try:
                            email_data["body"] += part.get_payload(decode=True).decode(errors="ignore")
                        except:
                            pass
            else:
                try:
                    email_data["body"] = message.get_payload(decode=True).decode(errors="ignore")
                except:
                    email_data["body"] = ""

            # Write each email as a separate JSON line
            out_f.write(json.dumps(email_data, ensure_ascii=False) + "\n")

print(f"All emails processed into {output_file}")
