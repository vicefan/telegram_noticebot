from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests
from bs4 import BeautifulSoup
import os
import telepot
import threading
from flask import Flask
import asyncio

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


# ===== 텔레그램 명령어 핸들러 =====
async def send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = get_notice_msg()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Send '/send' to get notices.")


async def rerun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global cached_msg
    cached_msg = get_notice_msg()
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Updating Database.")


# ===== Flask와 텔레그램 봇 동시에 실행 =====
def run_flask():
    app.run(host="0.0.0.0", port=3000)

def main():
    # Flask를 별도의 스레드에서 실행
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Telegram Bot 실행
    application = ApplicationBuilder().token(bot_token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("send", send))
    application.add_handler(CommandHandler("update", rerun))
    application.run_polling()

if __name__ == '__main__':
    main()