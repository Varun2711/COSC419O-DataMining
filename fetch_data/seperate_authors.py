import time
import json
import concurrent.futures
import requests
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {TOKEN}"} if TOKEN else {}

# Input
input_file = "commit_users.csv"
cache_file = "github_locations_cache.json"


# Load previous results (cache)
if os.path.exists(cache_file):
    with open(cache_file, "r", encoding="utf-8") as f:
        user_locations = json.load(f)
else:
    user_locations = {}

# Define countries for filtering
sweden_keywords = [
    "Sweden", "Sverige", "Stockholm", "Gothenburg", "Malmö",
    "Uppsala", "Lund", "Linköping", "Umeå", "Örebro", "Västerås",
    "Helsingborg", "Norrköping", "Jönköping", "Swedish"
]

uk_keywords = [
    "United Kingdom", "UK", "England", "Scotland", "Wales", "Northern Ireland",
    "London", "Manchester", "Birmingham", "Edinburgh", "Glasgow", "Liverpool",
    "Bristol", "Cardiff", "Belfast", "Leeds", "Sheffield", "Nottingham",
    "Newcastle", "Aberdeen", "Oxford", "Cambridge", "Britain", "British"
]

# Function to fetch user location
def get_github_location(username):
    if username in user_locations:  # ✅ Skip if already cached
        return user_locations[username]
    url = f"https://api.github.com/users/{username}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)

        if response.status_code == 200:
            location = response.json().get("location", "Unknown")
        elif response.status_code == 404:
            location = "User Not Found"
        elif response.status_code == 403:
            print("🚨 Rate limit exceeded! Pausing for 10 minutes...")
            time.sleep(60)  
            return get_github_location(username)  # Retry
        else:
            location = "Unknown"

        user_locations[username] = location  # Cache result

        # ✅ Save cache every 100 users to prevent losing progress
        if len(user_locations) % 100 == 0:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(user_locations, f)

        return location
    except requests.exceptions.RequestException:
        return "Unknown"
    
# Read commit users CSV file
if os.path.exists(input_file):
    df = pd.read_csv(input_file)

    # ✅ Filter users who haven't been fetched yet
    remaining_users = [row["Username"] for _, row in df.iterrows() if row["Username"] not in user_locations]

    print(f"🔍 Fetching locations for {len(remaining_users)} users (cached users skipped)...")

    # Fetch locations using multiple threads (5 threads to prevent rate limit)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_user = {executor.submit(get_github_location, username): username for username in remaining_users}

        for future in concurrent.futures.as_completed(future_to_user):
            username = future_to_user[future]
            try:
                user_locations[username] = future.result()
            except Exception as e:
                user_locations[username] = "Error"
                print(f"❌ Error fetching location for {username}: {e}")

    # ✅ Final cache save
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(user_locations, f)

    # Separate users by country
    sweden_authors = {}
    uk_authors = {}

    for index, row in df.iterrows():
        repo = row["Repository"]
        time_frame = row["Time Frame"]
        username = row["Username"]
        location = user_locations.get(username, "Unknown")

        if any(keyword in location for keyword in sweden_keywords):
            if repo not in sweden_authors:
                sweden_authors[repo] = []
            sweden_authors[repo].append((time_frame, username, location))

        if any(keyword in location for keyword in uk_keywords):
            if repo not in uk_authors:
                uk_authors[repo] = []
            uk_authors[repo].append((time_frame, username, location))

    # Save results for Sweden (in current directory)
    for repo, authors in sweden_authors.items():
        output_file = f"{repo}_authors_sweden.csv"
        df_sweden = pd.DataFrame(authors, columns=["Time Frame", "Username", "Location"])
        df_sweden.to_csv(output_file, index=False)
        print(f"✅ Saved Sweden authors for {repo} to {output_file}")

    # Save results for UK (in current directory)
    for repo, authors in uk_authors.items():
        output_file = f"{repo}_authors_uk.csv"
        df_uk = pd.DataFrame(authors, columns=["Time Frame", "Username", "Location"])
        df_uk.to_csv(output_file, index=False)
        print(f"✅ Saved UK authors for {repo} to {output_file}")

else:
    print(f"❌ File {input_file} not found!")