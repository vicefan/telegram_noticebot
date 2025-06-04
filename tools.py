import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from bs4 import BeautifulSoup
from datetime import datetime

def get_news_html():
    url = "https://news.naver.com/main/ranking/popularDay.naver"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    soup = BeautifulSoup(res.content, 'html.parser')

    # 뉴스 데이터 크롤링
    news_items = soup.find_all("ul", class_="rankingnews_list")[:10]
    news_names = [x.text for x in soup.find_all("strong", class_="rankingnews_name")][:10]
    datas = [{x: []} for x in news_names]

    for i in range(len(news_items)):
        news_item = news_items[i]
        news_title = news_item.find("a").text.strip()
        news_link = news_item.find("a")["href"]
        datas[i][news_names[i]].append(news_title)
        datas[i][news_names[i]].append(news_link)

    # HTML 생성
    html = """
    <html>
        <head>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    background-color: #f9f9f9;
                    color: #333;
                    padding: 20px;
                }
                .news-container {
                    max-width: 600px;
                    margin: auto;
                    background: #fff;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
                    padding: 20px;
                }
                .news-header {
                    text-align: center;
                    color: #4CAF50;
                    margin-bottom: 20px;
                }
                .news-item {
                    margin-bottom: 15px;
                    padding: 10px;
                    border-bottom: 1px solid #ddd;
                }
                .news-item:last-child {
                    border-bottom: none;
                }
                .news-title {
                    font-size: 18px;
                    font-weight: bold;
                    color: #2196F3;
                    text-decoration: none;
                }
                .news-title:hover {
                    text-decoration: underline;
                }
                .news-source {
                    font-size: 14px;
                    color: #555;
                }
                .gif-container {
                    text-align: center;
                    margin-bottom: 20px;
                }
            </style>
        </head>
        <body>
            <div class="news-container">
                <div class="gif-container">
                    <img src="https://i.ibb.co/27Kh0cQy/vice.gif" alt="공지사항 GIF" style="max-width: 100%; height: auto; border-radius: 5px;">
                </div>
                <h2 class="news-header">언론사 별 랭킹 1위 뉴스</h2>
    """

    for data in datas:
        for source, details in data.items():
            news_title = details[0]
            news_link = details[1]
            html += f"""
                <div class="news-item">
                    <div class="news-source">{source}</div>
                    <a href="{news_link}" class="news-title" target="_blank">{news_title}</a>
                </div>
            """

    html += """
            </div>
        </body>
    </html>
    """
    return html


# 이메일 전송
def send_email(sender_email, receiver_email, app_password, html):
    message = MIMEMultipart("alternative")
    message["Subject"] = f"{datetime.now().strftime('%Y-%m-%d')} 뉴스 크롤링"
    message["From"] = sender_email
    message["To"] = receiver_email

    message.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, message.as_string())