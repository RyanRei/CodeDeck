from fastapi import APIRouter, HTTPException, status,Response
import json
from bs4 import BeautifulSoup as bs
import requests


router = APIRouter(prefix="/g4g", tags=["geeksforgeeks"])


@router.get("/{username}/info")
async def get_g4g_data(username: str):
    profilePage = requests.get(f"https://www.geeksforgeeks.org/user/{username}/", headers={"User-Agent": "Mozilla/5.0"})

    soup = bs(profilePage.content, 'html.parser')

    script_tag = soup.find("script", id="__NEXT_DATA__", type="application/json")

    user_data = json.loads(script_tag.string)
    user_info = user_data["props"]["pageProps"]["userInfo"]
    #user_submissions = user_data["props"]["pageProps"]["userSubmissionsInfo"]

    generalInfo = {
                "userName": "speedcuberayush",
                "fullName": user_info.get("name", ""),
                "profilePicture": user_info.get("profile_image_url", ""),
                "institute": user_info.get("institute_name", ""),
                "instituteRank": user_info.get("institute_rank", ""),
                "currentStreak": user_info.get("pod_solved_longest_streak", "00"),
                "maxStreak": user_info.get("pod_solved_global_longest_streak", "00"),
                "codingScore": user_info.get("score", 0),
                "monthlyScore": user_info.get("monthly_score", 0),
                "totalProblemsSolved": user_info.get("total_problems_solved", 0),
                "contestRating": user_info.get("contest_rating", 0),
    }
    return {"generalInfo": generalInfo}



@router.get("/{username}/stats")
async def get_g4g_data(username: str):
    profilePage = requests.get(f"https://www.geeksforgeeks.org/user/{username}/", headers={"User-Agent": "Mozilla/5.0"})

    soup = bs(profilePage.content, 'html.parser')

    script_tag = soup.find("script", id="__NEXT_DATA__", type="application/json")

    user_data = json.loads(script_tag.string)
   
    user_submissions = user_data["props"]["pageProps"]["userSubmissionsInfo"]
    solvedStats = {}
    for difficulty, problems in user_submissions.items():
        questions = [
            {
                "question": details["pname"],
                "questionUrl": f"https://practice.geeksforgeeks.org/problems/{details['slug']}"
            }
            for details in problems.values()
        ]
        solvedStats[difficulty.lower()] = {"count": len(questions), "questions": questions}

    return {"solvedStats": solvedStats}
