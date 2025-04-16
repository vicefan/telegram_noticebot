import requests
from bs4 import BeautifulSoup

url_apsl = "https://apsl.inha.ac.kr/logistics/4465/subview.do"
headers = {"User-Agent": "Mozilla/5.0"}
res = requests.get(url_apsl, headers=headers)
soup = BeautifulSoup(res.content, 'html.parser')

table = soup.find("table", class_="artclTable artclHorNum1").find("tbody")
contents = [x for x in table.find_all("tr") if not x.attrs == {'class': ['headline']}]
td_title_apsl = [x.strong.text for x in contents]
td_date_apsl = [x.find("td", class_="_artclTdRdate").text for x in contents]

url_inha = "https://www.inha.ac.kr/kr/950/subview.do"
res = requests.get(url_inha, headers=headers)
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

print(msg)