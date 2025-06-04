import time
import os
from dotenv import load_dotenv
import schedule
from tools import get_news_html, send_email

load_dotenv()

mail_adr = os.getenv("MAIL")
app_pwd = os.getenv("APP_PW")
email_address = os.getenv("RECEIVER")

EMAIL_TIME = "10:00"

def send():
    html = get_news_html()
    send_email(
        sender_email=mail_adr,
        receiver_email=email_address,
        app_password=app_pwd,
        html=html
    )

def run_schedule():
    schedule.clear()
    schedule.every().day.at(EMAIL_TIME).do(send)
    while True:
        schedule.run_pending()
        time.sleep(1)

def main():
    run_schedule()

if __name__ == "__main__":
    main()
