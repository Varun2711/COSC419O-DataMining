import requests
import csv
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("GITHUB_TOKEN")

repositories = [
    ("freeCodeCamp", "freeCodeCamp"),
    ("pytorch","pytorch"),
    ("facebook","react"),
    ("vuejs", "vue"),
    ("microsoft", "vscode"),
]

HEADERS = {"Authorization": f"token {TOKEN}"} if TOKEN else {}

# Timeline
time_frames = [
    ("2018-01-01T00:00:00Z", "2019-12-31T23:59:59Z"),
    ("2020-01-01T00:00:00Z", "2022-06-30T23:59:59Z"),
    ("2022-06-01T00:00:00Z", "2024-06-30T23:59:59Z"),
]

# fetch timeline
def fetch_commits(owner, repo, since, until):
    BASE_URL = f"https://api.github.com/repos/{owner}/{repo}/commits"
    per_page = 100  
    page = 1
    all_commits = []
    repo_shortname = repo.lower()
    filename = f"commits_{since[:4]}_{until[:4]}_{repo_shortname}.csv"

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

        for commit in commits:
            author_name = commit["commit"]["author"]["name"]
            author_username = commit["author"]["login"] if commit.get("author") else "Unknown"  # Extract GitHub username

            all_commits.append([
                commit["sha"],
                commit["commit"]["message"],
                author_name,
                author_username,  # Add username
                commit["commit"]["author"]["date"]
            ])

        print(f"✅ Fetched {len(commits)} commits from page {page} for {owner}/{repo}")
        page += 1  # go to next page

    # Save 
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["SHA", "Message", "Author", "Username", "Date"])

        for commit in all_commits:
            writer.writerow(commit)

    print(f"✅ Saved {len(all_commits)} commits to {filename}")

# Fetch commits for each timeline
for owner, repo in repositories:
    for since, until in time_frames:
        fetch_commits(owner, repo, since, until)