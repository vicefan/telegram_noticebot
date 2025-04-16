from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests
from bs4 import BeautifulSoup
import os
import telepot
import threading
from flask import Flask
import asyncio
from dotenv import load_dotenv
import json
import schedule
import time

load_dotenv()

app = Flask(__name__)
bot_token = os.getenv("TOKEN")
chat_id = os.getenv("CHAT_ID")


# ===== 공통 크롤링 함수 =====
def get_notice_msg():
    try:
        url_apsl = "https://apsl.inha.ac.kr/logistics/4465/subview.do"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url_apsl, headers=headers)
        res.raise_for_status()  # HTTP 에러 확인
        soup = BeautifulSoup(res.content, 'html.parser')

        table = soup.find("table", class_="artclTable artclHorNum1").find("tbody")
        contents = [x for x in table.find_all("tr") if not x.attrs == {'class': ['headline']}]
        td_title_apsl = [x.strong.text for x in contents]
        td_date_apsl = [x.find("td", class_="_artclTdRdate").text for x in contents]

        url_inha = "https://www.inha.ac.kr/kr/950/subview.do"
        res = requests.get(url_inha, headers=headers)
        res.raise_for_status()  # HTTP 에러 확인
        soup = BeautifulSoup(res.content, 'html.parser')
        table = soup.find("table", class_="artclTable artclHorNum1").find("tbody")
        contents = [x for x in table.find_all("tr") if not x.attrs == {'class': ['headline']}]
        td_title_inha = [x.get_text(separator="sep", strip=True).split("sep")[1] for x in contents]
        td_date_inha = [x.find("td", class_="_artclTdRdate").text for x in contents]

        result_apsl = [f"{td_title_apsl[i]} // {td_date_apsl[i]}" for i in range(len(td_title_apsl))]
        result_inha = [f"{td_title_inha[i]} // {td_date_inha[i]}" for i in range(len(td_title_inha))]

        msg = (
            "🗒️ 공지사항 정리 🗒️\n\n"
            "[아태물류학부 공지]\n✅" + "\n✅".join(result_apsl) + "\n\n"
            "[인하대학교 공지]\n☑️" + "\n☑️".join(result_inha) + "\n\n"
            f"🔗아태: {url_apsl}\n🔗인하: {url_inha}"
        )
        return msg
    except Exception as e:
        return f"공지사항을 불러오는 데 실패했습니다: {str(e)}"
    
def save_log(chat_id, command):
    local_time = time.localtime()
    formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", local_time)
    if not os.path.exists("log.json"):
        with open("log.text", "a") as f:
            f.write(f"Chat ID: {chat_id}, Command: {command}, Time: {formatted_time}\n")


# ===== Flask 라우터 =====
cached_msg = "공지사항을 불러오는 중입니다. 잠시만 기다려주세요."

@app.before_request
def before_request():
    global cached_msg
    try:
        cached_msg = get_notice_msg()
    except Exception as e:
        cached_msg = f"공지사항을 불러오는 데 실패했습니다: {str(e)}"

@app.route("/")
def home():
    return "봇이 작동 중입니다! /sendmsg 호출 시 공지사항 발송"

@app.route("/sendmsg")
def sendmsg():
    global cached_msg
    bot = telepot.Bot(token=bot_token)
    bot.sendMessage(chat_id, cached_msg)
    return "공지사항을 텔레그램으로 전송했어요!"

# @app.route("/clear_all_time_data")
# def clear_all_time_data():
#     try:
#         if os.path.exists(TIME_FILE):
#             with open(TIME_FILE, "r") as f:
#                 time_data = json.load(f)
#             os.remove(TIME_FILE)
#         return f"모든 시간 데이터가 삭제되었습니다. \n\n{time_data}"
#     except Exception as e:
#         return f"시간 데이터 삭제에 실패했습니다: {str(e)}"

@app.route("/log")
def log():
    try:
        if os.path.exists("log.json"):
            with open("log.json", "r") as f:
                log_data = f.read()
            return log_data
        else:
            return "로그 파일이 존재하지 않습니다."
    except Exception as e:
        return f"로그 파일을 읽는 데 실패했습니다: {str(e)}"

# ===== 텔레그램 명령어 핸들러 =====
async def send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global cached_msg
    save_log(update.effective_chat.id, "/send")
    if cached_msg == "공지사항을 불러오는 중입니다. 잠시만 기다려주세요.":
        cached_msg = get_notice_msg()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=cached_msg)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_log(update.effective_chat.id, "/start")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Send '/send' to get notices.")


async def rerun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global cached_msg
    save_log(update.effective_chat.id, "/update")
    if cached_msg == "공지사항을 불러오는 중입니다. 잠시만 기다려주세요.":
        cached_msg = get_notice_msg()
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Updating Database.")


# ===== Flask와 텔레그램 봇 동시에 실행 =====
TIME_FILE = "time_usr.json"

# 시간 설정 저장 함수
def save_time(chat_id, user_time):
    try:
        if not os.path.exists(TIME_FILE):
            with open(TIME_FILE, "w") as f:
                json.dump({}, f)

        with open(TIME_FILE, "r") as f:
            time_data = json.load(f)

        time_data[str(chat_id)] = user_time

        with open(TIME_FILE, "w") as f:
            json.dump(time_data, f)
    except Exception as e:
        telepot.Bot(token=bot_token).sendMessage(chat_id, "Error:\n" + str(e))

# 시간 불러오기 함수
def load_times():
    if not os.path.exists(TIME_FILE):
        return {}
    with open(TIME_FILE, "r") as f:
        return json.load(f)

# 스케줄링 작업
def schedule_task():
    def send_scheduled_message(chat_id):
        global cached_msg
        bot = telepot.Bot(token=bot_token)
        cached_msg = get_notice_msg()
        bot.sendMessage(chat_id, cached_msg)

    # 기존 스케줄을 초기화
    schedule.clear()

    # time_usr.json에서 사용자별 시간을 읽어와 작업 예약
    time_data = load_times()
    for chat_id, user_time in time_data.items():
        schedule.every().day.at(user_time).do(send_scheduled_message, chat_id=int(chat_id))


# # /settime 명령어 핸들러
# async def set_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     save_log(update.effective_chat.id, "/settime")
#     try:
#         user_time = context.args[0]  # HH:MM 형식으로 입력받음
#         chat_id = update.effective_chat.id

#         # 시간 형식 검증
#         time.strptime(user_time, "%H:%M")

#         # 시간 저장
#         save_time(chat_id, user_time)

#         # 스케줄 업데이트
#         schedule_task()

#         await context.bot.send_message(chat_id=chat_id, text=f"time set to {user_time}")
#     except (IndexError, ValueError):
#         await context.bot.send_message(chat_id=update.effective_chat.id, text="format: /settime HH:MM")

def run_flask():
    app.run(host="0.0.0.0", port=3000)

def main():
    # Flask를 별도의 스레드에서 실행
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # # 스케줄러를 별도의 스레드에서 실행
    # schedule_thread = threading.Thread(target=schedule_task)
    # schedule_thread.daemon = True
    # schedule_thread.start()

    # Telegram Bot 실행
    application = ApplicationBuilder().token(bot_token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("send", send))
    application.add_handler(CommandHandler("update", rerun))
    # application.add_handler(CommandHandler("settime", set_time))  # /settime 명령어 추가
    application.run_polling()

if __name__ == '__main__':
    main()