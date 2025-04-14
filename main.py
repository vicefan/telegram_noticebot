from flask import Flask
import requests
from bs4 import BeautifulSoup
import os
import telepot

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

app = Flask(__name__)


class Telegram:
    def __init__(self):
        self.bot = telepot.Bot(token=TOKEN)

    def sendMessage(self, message):
        self.bot.sendMessage(os.getenv("CHAT_ID"), message)

    @staticmethod
    def update_msg():
        url_apsl = "https://apsl.inha.ac.kr/logistics/4465/subview.do"
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(url_apsl, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')

        td_title_apsl = [title.find("strong").text for title in soup.find_all("td", class_="_artclTdTitle")][2:]
        td_date_apsl = [title.text for title in soup.find_all("td", class_="_artclTdRdate")][2:]

        url_inha = "https://www.inha.ac.kr/kr/950/subview.do"
        
        response = requests.get(url_inha, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')

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


@app.route("/")
def home():
    return "봇이 작동 중입니다! /send로 접속하면 텔레그램 알림을 보냅니다."


@app.route("/send")
def send_notice():
    bot = Telegram()
    msg = bot.update_msg()
    bot.sendMessage(msg)
    return "공지사항을 텔레그램으로 전송했어요!"


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=3000)