from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
import requests


# 토큰을 bot_token 변수에 저장
bot_token = '7740506271:AAFBPW0-YX91kXIvnQOshElW3mW2ncZb9MQ'


# start 명령어 처리 함수
async def send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = "https://44c12bce-9acf-44c9-83fa-3dec01d9eec7-00-3bvwipr0c4ky8.sisko.replit.dev/sendmsg"

    await context.bot.send_message(chat_id=update.effective_chat.id, text=requests.get(url).text)


if __name__ == '__main__':
    # 챗봇 application 인스턴스 생성
    application = ApplicationBuilder().token(bot_token).build()

    # start 핸들러 생성
    start_handler = CommandHandler('send', send)

    # 핸들러 추가
    application.add_handler(start_handler)

    # 폴링 방식으로 실행
    application.run_polling()