import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from bs4 import BeautifulSoup
from collections import defaultdict
from datetime import datetime

# 날짜별 공지사항 그룹화
def group_notices_by_date(titles, dates):
    grouped_notices = defaultdict(list)
    for title, date in zip(titles, dates):
        grouped_notices[date].append(title)
    return grouped_notices

# HTML 생성
def format_grouped_notices_as_html(grouped_notices, section_title, url):
    html = f"""
    <h3 style="color: #2196F3;">{section_title}</h3>
    <ul style="list-style-type: none; padding: 0; margin: 0;">
    """
    for date, notices in grouped_notices.items():
        html += f"""
        <li style="margin-bottom: 10px;">
            <strong>{date}</strong>
            <ul style="list-style-type: none; padding-left: 20px; margin: 0;">
        """
        for notice in notices:
            html += f"<li style='margin-bottom: 5px;'>✅ {notice}</li>"
        html += "</ul></li>"
    html += f"""
    </ul>
    <p style="margin-top: 10px;">🔗 <a href="{url}" style="color: #FF5722; text-decoration: none;">{section_title} 바로가기</a></p>
    """
    return html

# 공지사항 크롤링
def get_notice_msg():
    try:
        url_apsl = "https://apsl.inha.ac.kr/logistics/4465/subview.do"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url_apsl, headers=headers)
        res.raise_for_status()
        soup = BeautifulSoup(res.content, 'html.parser')

        table = soup.find("table", class_="artclTable artclHorNum1").find("tbody")
        contents = [x for x in table.find_all("tr") if not x.attrs == {'class': ['headline']}]
        td_title_apsl = [x.strong.text for x in contents]
        td_date_apsl = [x.find("td", class_="_artclTdRdate").text for x in contents]

        url_inha = "https://www.inha.ac.kr/kr/950/subview.do"
        res = requests.get(url_inha, headers=headers)
        res.raise_for_status()
        soup = BeautifulSoup(res.content, 'html.parser')
        table = soup.find("table", class_="artclTable artclHorNum1").find("tbody")
        contents = [x for x in table.find_all("tr") if not x.attrs == {'class': ['headline']}]
        td_title_inha = [x.get_text(separator="sep", strip=True).split("sep")[1] for x in contents]
        td_date_inha = [x.find("td", class_="_artclTdRdate").text for x in contents]

        grouped_apsl = group_notices_by_date(td_title_apsl, td_date_apsl)
        grouped_inha = group_notices_by_date(td_title_inha, td_date_inha)

        html_apsl = format_grouped_notices_as_html(grouped_apsl, "아태물류학부 공지", url_apsl)
        html_inha = format_grouped_notices_as_html(grouped_inha, "인하대학교 공지", url_inha)

        html = f"""
        <html>
            <body>
                <h2>🗒️ 공지사항 정리 🗒️</h2>
                {html_apsl}
                {html_inha}
            </body>
        </html>
        """
        return html
    except Exception as e:
        return f"공지사항을 불러오는 데 실패했습니다: {str(e)}"

# 이메일 전송
def send_email(sender_email, receiver_email, app_password, html):
    message = MIMEMultipart("alternative")
    message["Subject"] = f"{datetime.now().strftime('%Y-%m-%d')} 공지사항 업데이트"
    message["From"] = sender_email
    message["To"] = receiver_email

    message.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, message.as_string())

# 로그 저장
def save_log(chat_id, command):
    local_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"Chat ID: {chat_id}, Command: {command}, Time: {local_time}\n"
    with open("log.txt", "a") as f:
        f.write(log_entry)