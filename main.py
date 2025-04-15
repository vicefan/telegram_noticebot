from flask import Flask, g
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests
from bs4 import BeautifulSoup
import os
import telepot
import threading  # Flask랑 Bot 동시 실행

app = Flask(__name__)
bot_token = os.getenv("TOKEN")
chat_id = os.getenv("CHAT_ID")


# ===== 공통 크롤링 함수 =====
def get_notice_msg():
    url_apsl = "https://apsl.inha.ac.kr/logistics/4465/subview.do"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url_apsl, headers=headers)
    soup = BeautifulSoup(res.content, 'html.parser')
    td_title_apsl = [title.find("strong").text for title in soup.find_all("td", class_="_artclTdTitle")][2:]
    td_date_apsl = [title.text for title in soup.find_all("td", class_="_artclTdRdate")][2:]

    url_inha = "https://www.inha.ac.kr/kr/950/subview.do"
    res = requests.get(url_inha, headers=headers)
    soup = BeautifulSoup(res.content, 'html.parser')
    td_title_inha = [title.get_text(separator="sep", strip=True).split("sep")[0]
                     for title in soup.find_all("td", class_="_artclTdTitle")][3:]
    td_date_inha = [title.text for title in soup.find_all("td", class_="_artclTdRdate")][3:]

    result_apsl = [f"{td_title_apsl[i]} // {td_date_apsl[i]}" for i in range(len(td_title_apsl))]
    result_inha = [f"{td_title_inha[i]} // {td_date_inha[i]}" for i in range(len(td_title_inha))]

    msg = (
        "🗒️ 공지사항 정리 🗒️\n\n"
        "[아태물류학부 공지]\n✅" + "\n✅".join(result_apsl) + "\n\n"
        "[인하대학교 공지]\n☑️" + "\n☑️".join(result_inha) + "\n\n"
        f"🔗아태: {url_apsl}\n🔗인하: {url_inha}"
    )
    return msg


# ===== Flask 라우터 =====
@app.before_request
def before_request():
    g.msg = get_notice_msg()


@app.route("/")
def home():
    return "봇이 작동 중입니다! /sendmsg 호출 시 공지사항 발송"

@app.route("/sendmsg")
def sendmsg():
    bot = telepot.Bot(token=bot_token)
    bot.sendMessage(chat_id, g.msg)
    return "공지사항을 텔레그램으로 전송했어요!"


# ===== 텔레그램 명령어 핸들러 =====
async def send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = get_notice_msg()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)


# ===== Flask와 텔레그램 봇 동시에 실행 =====
def run_flask():
    app.run(host="0.0.0.0", port=3000)


if __name__ == '__main__':
    threading.Thread(target=run_flask).start()  # Flask 병렬 실행
    application = ApplicationBuilder().token(bot_token).build()
    application.add_handler(CommandHandler("send", send))
    application.run_polling()