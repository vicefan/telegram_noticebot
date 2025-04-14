import telepot
import requests
from bs4 import BeautifulSoup


class Telegram():
    def __init__(self):
        my_token = "7740506271:AAFBPW0-YX91kXIvnQOshElW3mW2ncZb9MQ"
        self.bot = telepot.Bot(token=my_token)

    def sendMessage(self, message):
        self.bot.sendMessage("8024833881", message)

    def getUpdates(self):
        return self.bot.getUpdates()

    @staticmethod
    def update_msg():
        url_apsl = "https://apsl.inha.ac.kr/logistics/4465/subview.do"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }

        response = requests.get(url_apsl, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')

        td_title_apsl = [title.find("strong").text for title in soup.find_all("td", class_="_artclTdTitle")][2:]
        td_date_apsl = [title.text for title in soup.find_all("td", class_="_artclTdRdate")][2:]

        url_inha = "https://www.inha.ac.kr/kr/950/subview.do"

        response = requests.get(url_inha, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')

        td_title_inha = [title.get_text(separator="sep", strip=True).split("sep")[0] for title in
                         soup.find_all("td", class_="_artclTdTitle")][3:]
        td_date_inha = [title.text for title in soup.find_all("td", class_="_artclTdRdate")][3:]

        # 크롤링한 데이터 정리
        result_apsl = []
        result_inha = []
        for i in range(len(td_title_apsl)):
            result_apsl.append(f"{td_title_apsl[i]} // {td_date_apsl[i]}")
        for i in range(len(td_title_inha)):
            result_inha.append(f"{td_title_inha[i]} // {td_date_inha[i]}")

        return f"🗒️ 공지사항 정리 🗒️\n\n[아태물류학부 공지]\n✅{"\n✅".join(result_apsl)}\n\n[인하대학교 공지]\n☑️{"\n☑️".join(result_inha)}\n\n🔗아태: {url_apsl}\n🔗인하: {url_inha}"


if __name__ == '__main__':
    bot = Telegram()
    msg = Telegram.update_msg()
    bot.sendMessage(msg)  # 메시지 보내기
