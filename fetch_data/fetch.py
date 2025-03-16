import requests
import csv
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("GITHUB_TOKEN")

# Repo
OWNER = "freeCodeCamp"
REPO = "freeCodeCamp"
BRANCH = "main"

HEADERS = {"Authorization": f"token {TOKEN}"} if TOKEN else {}

# Timeline
time_frames = [
    ("2018-01-01T00:00:00Z", "2019-12-31T23:59:59Z", "commits_2018_2019_fcc.csv"),
    ("2020-01-01T00:00:00Z", "2022-06-30T23:59:59Z", "commits_2020_2022_fcc.csv"),
    ("2022-06-01T00:00:00Z", "2024-06-30T23:59:59Z", "commits_2022_2024_fcc.csv"),
]

# fetch timeline
def fetch_commits(since, until, filename):
    BASE_URL = f"https://api.github.com/repos/{OWNER}/{REPO}/commits"
    per_page = 100  
    page = 1
    all_commits = []

    
    while True:
        # Fetch commits on current page
        URL = f"{BASE_URL}?since={since}&until={until}&per_page={per_page}&page={page}"
        response = requests.get(URL, headers=HEADERS)

        if response.status_code != 200:
            print(f"Failed to fetch commits ({filename}): {response.status_code} - {response.text}")
            break

        commits = response.json()
        
        if not commits:
            break  

        all_commits.extend(commits)
        print(f"Fetched {len(commits)} commits from page {page} for {filename}")

        page += 1  # go to next page

    # Save 
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["SHA", "Message", "Author", "Date"])

        for commit in all_commits:
            writer.writerow([
                commit["sha"],
                commit["commit"]["message"],
                commit["commit"]["author"]["name"],
                commit["commit"]["author"]["date"]
            ])

    print(f"✅ Saved {len(all_commits)} commits to {filename}")

# Fetch commits for each timeline
for since, until, filename in time_frames:
    fetch_commits(since, until, filename)