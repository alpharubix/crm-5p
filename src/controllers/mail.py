import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from src.config import settings


def create_smtp_connection():
    try:
            smtp = smtplib.SMTP('smtp.zoho.com', 587, timeout=10)
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            app_password = settings.APP_PASSWORD
            print(app_password)
            smtp.login('techmgr@meramerchant.com', app_password)
            print("SMTP connection created successfully.")
            return smtp
    except Exception as e:
        print("Error creating SMTP connection:", e)
        return None


def prepare_mail_body(module_name, parent_id,user_name,note):

        html_content = f"""
        <p>Dear User,</p>
        
        <p>You have been mentioned in a note. Please review the details below:</p>
        
        <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse;">
        <tr>
        <td><strong>Module</strong></td>
        <td>{module_name}</td>
        </tr>
        
        <tr>
        <td><strong>Link to see the note</strong></td>
        <td>https://r1xchange-crm.netlify.app/{module_name}/{parent_id}</td>
        </tr>
        
        <tr>
        <td><strong>Mentioned By user</strong></td>
        <td>{user_name}</td>
        </tr>
        
        <tr>
        <td><strong>Note</strong></td>
        <td>{note}</td>
        </tr>
        </table>
        
        <p>Please log in to the CRM system to take necessary action.</p>
        
        <p>Regards,<br>
        R1xchange CRM SERVER</p>
        """

        return html_content


def process_mention_emails(email_list):
    ready_emails = []
    for email in email_list:
        mail = {"email_address":email.get('user_email_address'),"body":prepare_mail_body(module_name=email.get('module'),parent_id=email.get('entity_id'),user_name=email.get('user_name'),note=email.get('note'))}
        ready_emails.append(mail)
    send_email(ready_emails)
    return None


def send_email(email_list):
        try:
            smtp = create_smtp_connection()
            for email in email_list:
                msg = MIMEMultipart()

                msg['From'] = "R1xchange Crm mail service <techmgr@meramerchant.com>"
                msg['To'] = email["email_address"]
                msg['Subject'] = "You were mentioned in a note"

                msg.attach(MIMEText(email["body"], 'html'))
                try:
                    smtp.send_message(msg)
                    print(f"Email sent successfully to {email['email_address']}")
                except Exception as e:
                    print(f"Error sending email to {email['email_address']}:", e)

            smtp.quit()
            return None

        except Exception as e:
            print("SMTP connection failed:", e)
            return None
