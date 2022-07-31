import urllib.request

import bs4


url = "https://www.ptt.cc/bbs/Python/index442.html"
request = urllib.request.Request(
    url,
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/93.0.4577.82 Safari/537.36"
    },
)

with urllib.request.urlopen(request) as response:
    data = response.read().decode("utf-8")

soup = bs4.BeautifulSoup(data, "html.parser")

for title in soup.select("div.title"):
    print(title.a.get_text())
