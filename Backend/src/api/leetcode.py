import requests
from bs4 import BeautifulSoup
res=requests.get("https://alfa-leetcode-api.onrender.com/hxu10/solved")

d=res.json()

print(d)