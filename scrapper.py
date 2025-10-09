from fastapi import FastAPI
import requests
from bs4 import BeautifulSoup

app = FastAPI()

@app.get("/scrape")
def scrape_site():
    url = "https://example.com"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    title = soup.find("h1").text
    return {"title": title}

username = input("Enter Username: ")
url = "https://codeforces.com/api/user.info"
params = {"handles": username}
params2 = {"handle": username}
response = requests.get(url, params=params)
data = response.json()
if data["status"] == "OK":
    user_info = data["result"][0]
    print("Handle:", user_info["handle"])
    print("Rating:", user_info["rating"])
    print("Max Rating:", user_info["maxRating"])
else:
    print("Error:", data["comment"])


url2 = "https://codeforces.com/api/user.rating"
response2=requests.get(url2, params=params2)
data2=response2.json()
if data2["status"] == "OK":
    for contest in data2["result"]:
        print("Contest ID:", contest["contestId"])
        print("Rank:", contest["rank"])
        print("Rating Change:", contest["newRating"] - contest["oldRating"])
else:
    print("Error:", data2["comment"])
'''
url = "https://www.codechef.com/users/potato167"
response = requests.get(url)   # Fetch page content
html_content = response.text   

soup = BeautifulSoup(html_content, "html.parser")
title = soup.title.text
print(title)

for link in soup.find_all("a"):
    print(link.get("href"))'''