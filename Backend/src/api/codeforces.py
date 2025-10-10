from fastapi import APIRouter, HTTPException, status,Response
import json
from bs4 import BeautifulSoup as bs
import requests


router = APIRouter(prefix="/cfcs", tags=["codeforces"])


@router.get("/{username}/info")
async def get_codeforces_info(username: str):
    res=requests.get(f"https://codeforces.com/api/user.info?handles={username}")
    if res.status_code == 200:
        data = res.json()
        if data["status"] == "OK":
            user_info = data["result"][0]
            return {
                "userName": user_info["handle"],
                "fullName": user_info["firstName"] + " " + user_info["lastName"],
                "profilePicture": user_info["titlePhoto"],
                "rating": user_info["rating"],
                "rank": user_info["rank"],
                "maxRating": user_info["maxRating"],
                "maxRank": user_info["maxRank"],
            }
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

@router.get("/{username}/rating")
async def get_codeforces_rating(username: str):
    res=requests.get(f"https://codeforces.com/api/user.rating?handle={username}")
    if res.status_code == 200:
        data = res.json()
        if data["status"] == "OK":
            rating_changes = data["result"]
            rating_history = [
                {
                    "contestId": change["contestId"],
                    "contestName": change["contestName"],
                    "rank": change["rank"],
                    "oldRating": change["oldRating"],
                    "newRating": change["newRating"],
                    "ratingUpdateTimeSeconds": change["ratingUpdateTimeSeconds"]
                }
                for change in rating_changes
            ]
            return {"ratingHistory": rating_history}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@router.get("/{username}/status")
async def get_codeforces_rating(username: str):
    res=requests.get(f"https://codeforces.com/api/user.status?handle={username}&from=1&count=10")
    if res.status_code == 200:
        data = res.json()
        if data["status"] == "OK":
            submissions = data["result"]
            
            return {"submissions": submissions}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")