import smtplib
from email.message import EmailMessage

def send_direct_email():
    # Configure these values
    smtp_server = 'smtp.sendgrid.net'
    smtp_port = 587
    smtp_username = 'apikey'  # Literally the word 'apikey'
    smtp_password = 'YOUR_SENDGRID_API_KEY_HERE'  # Replace with your actual key
    from_email = 'b00147423@mytudublin.ie'  # Must be verified in SendGrid
    to_email = 'your-personal-email@gmail.com'  # Where you want to receive test
    
    msg = EmailMessage()
    msg.set_content("This is a raw SMTP test")
    msg['Subject'] = 'DIRECT SMTP TEST'
    msg['From'] = from_email
    msg['To'] = to_email

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        print("✅ Email sent successfully via raw SMTP!")
    except Exception as e:
        print(f"❌ SMTP FAILURE: {str(e)}")

if __name__ == '__main__':
    send_direct_email()