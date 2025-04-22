import time
from flask import Flask, send_file, abort, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from tools import get_notice_msg, save_log, send_email
import os
from dotenv import load_dotenv
import threading
import schedule
import json

load_dotenv()

app = Flask(__name__)
bot_token = os.getenv("TOKEN")
chat_id = os.getenv("CHAT_ID")
mail_adr = os.getenv("MAIL")
app_pwd = os.getenv("APP_PW")
EMAIL_TIME = "09:50"

EMAIL_SCHEDULE_FILE = "email_schedule.json"

# 이메일 스케줄 저장 함수
def save_email_schedule(chat_id, email_address):
    try:
        # JSON 파일이 없으면 생성
        if not os.path.exists(EMAIL_SCHEDULE_FILE):
            with open(EMAIL_SCHEDULE_FILE, "w") as f:
                json.dump({}, f)

        # 기존 스케줄 불러오기
        with open(EMAIL_SCHEDULE_FILE, "r") as f:
            schedules = json.load(f)

        # 이메일 주소 저장
        schedules[str(chat_id)] = email_address

        # 스케줄 저장
        with open(EMAIL_SCHEDULE_FILE, "w") as f:
            json.dump(schedules, f, indent=4)

    except Exception as e:
        print(f"Error saving email schedule: {e}")

# 이메일 스케줄 불러오기
def load_email_schedules():
    if not os.path.exists(EMAIL_SCHEDULE_FILE):
        return {}
    with open(EMAIL_SCHEDULE_FILE, "r") as f:
        return json.load(f)

# 스케줄링 작업
def schedule_email_tasks():
    schedules = load_email_schedules()
    for chat_id, email_address in schedules.items():
        schedule.every().day.at(EMAIL_TIME).do(send_scheduled_email, chat_id, email_address)

# 예약된 이메일 전송 함수
def send_scheduled_email(chat_id, email_address):
    html = get_notice_msg()
    send_email(
        sender_email=mail_adr,
        receiver_email=email_address,
        app_password=app_pwd,
        html=html
    )
    print(f"이메일이 {email_address}로 전송되었습니다!")

@app.before_request
def verify_token():
    token = os.getenv("KEY")
    if request.args.get("key") != token:
        abort(403)
        print("key error")

@app.route("/")
def home():
    return send_file("vice.gif", mimetype="image/gif")

@app.route("/notice")
def notice():
    return get_notice_msg()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_log(update.effective_chat.id, "/start")
    with open("vice.gif", "rb") as img:
        await context.bot.send_message(chat_id=update.effective_chat.id, photo=img, caption="viceversa")


# /email 명령어 핸들러
async def email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        e_adr = context.args[0]  # 이메일 주소 가져오기
        chat_id = update.effective_chat.id

        # 이메일 스케줄 저장
        save_email_schedule(chat_id, e_adr)

        # 스케줄 업데이트
        schedule.clear()  # 기존 스케줄 초기화
        schedule_email_tasks()

        await context.bot.send_message(chat_id=chat_id, text=f"이메일 {e_adr}로 매일 {EMAIL_TIME}에 공지사항이 전송됩니다.")
    except IndexError:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="이메일 주소를 입력해주세요. 예: /email example@example.com")
    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"오류 발생: {e}")


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        key = context.args[0]
        value = context.args[1]

        if not os.path.exists(EMAIL_SCHEDULE_FILE):
            with open(EMAIL_SCHEDULE_FILE, "w") as f:
                json.dump({}, f)
        
        with open(EMAIL_SCHEDULE_FILE, "r") as f:
            schedules = json.load(f)

        schedules[key] = value

        with open(EMAIL_SCHEDULE_FILE, "w") as f:
            json.dump(schedules, f, indent=4)

        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"이메일 {value}로 매일 {EMAIL_TIME}에 공지사항이 전송됩니다.")
    except IndexError:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="이메일 주소를 입력해주세요. 용법: /add name email")


async def send_me_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_log(update.effective_chat.id, "/send_email")
    html = get_notice_msg()
    print(f"이메일이 {context.args[0]}로 전송됩니다!")
    send_email(
        sender_email=mail_adr,
        receiver_email=context.args[0],
        app_password=app_pwd,
        html=html
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text="이메일이 전송되었습니다!")

# /delete 명령어 핸들러
async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id

        # 기존 스케줄 불러오기
        schedules = load_email_schedules()

        # 사용자의 이메일 스케줄 삭제
        if str(chat_id) in schedules:
            del schedules[str(chat_id)]

            # 스케줄 저장
            with open(EMAIL_SCHEDULE_FILE, "w") as f:
                json.dump(schedules, f, indent=4)

            # 스케줄 업데이트
            schedule.clear()
            schedule_email_tasks()

            await context.bot.send_message(chat_id=chat_id, text="이메일 스케줄이 삭제되었습니다.")
        else:
            await context.bot.send_message(chat_id=chat_id, text="등록된 이메일 스케줄이 없습니다.")
    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"오류 발생: {e}")


# 스케줄 실행 루프
def run_schedule():
    schedule.clear()
    schedule_email_tasks()
    while True:
        schedule.run_pending()
        time.sleep(1)

def run_flask():
    app.run(host="0.0.0.0", port="3000")

def main():
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # 스케줄러 실행
    schedule_thread = threading.Thread(target=run_schedule)
    schedule_thread.daemon = True
    schedule_thread.start()

    # Telegram Bot 실행
    application = ApplicationBuilder().token(bot_token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("email", email))
    application.add_handler(CommandHandler("delete", delete))
    application.add_handler(CommandHandler("send_email", send_me_email))
    application.add_handler(CommandHandler("add", add))
    application.run_polling()

if __name__ == "__main__":
    main()
