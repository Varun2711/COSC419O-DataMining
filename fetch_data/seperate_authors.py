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

# Input Files
input_file = "commit_users_3.csv"
cache_file = "github_locations_cache.json"

# Load previous results (cache)
if os.path.exists(cache_file):
    with open(cache_file, "r", encoding="utf-8") as f:
        user_data = json.load(f)
else:
    user_data = {}

# Define Sweden & UK keywords
sweden_keywords = [
    "Sweden", "Sverige", "Stockholm", "Gothenburg", "Malmö",
    "Uppsala", "Lund", "Linköping", "Umeå", "Örebro", "Västerås",
    "Helsingborg", "Norrköping", "Jönköping", "Swedish"
]

uk_keywords = [
    "United Kingdom", "UK", "England", "Scotland", "Wales", "Northern Ireland",
    "London", "Manchester", "Birmingham", "Edinburgh", "Glasgow", "Liverpool",
    "Bristol", "Cardiff", "Belfast", "Leeds", "Sheffield", "Nottingham",
    "Newcastle", "Aberdeen", "Oxford", "Cambridge", "Britain"
]

# Function to fetch user location and email
def get_github_user_info(username):
    if username in user_data:  # ✅ Skip if already cached
        return user_data[username]

    url = f"https://api.github.com/users/{username}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)

        if response.status_code == 200:
            data = response.json()  
            location = data.get("location", "Unknown") 
            email = data.get("email", "Unknown")

            user_data[username] = {"location": location, "email": email}

        elif response.status_code == 404:
            user_data[username] = {"location": "User Not Found", "email": "User Not Found"}

        elif response.status_code == 403:
            print("🚨 Rate limit exceeded! Pausing for 60 minutes...")
            time.sleep(3600)  
            return get_github_user_info(username)  # Retry

        else:
            user_data[username] = {"location": "Unknown", "email": "Unknown"}

        #  Save cache every 100 users 
        if len(user_data) % 100 == 0:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(user_data, f)

        return user_data[username]

    except requests.exceptions.RequestException:
        return {"location": "Unknown", "email": "Unknown"}

    
# Read commit users CSV file
if os.path.exists(input_file):
    df = pd.read_csv(input_file)

    # ✅ Filter users who haven't been fetched yet
    remaining_users = [row["Username"] for _, row in df.iterrows() if row["Username"] not in user_data]

    print(f"🔍 Fetching locations for {len(remaining_users)} users (cached users skipped)...")

    # Fetch locations using multiple threads (5 threads to prevent rate limit)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_user = {executor.submit(get_github_user_info, username): username for username in remaining_users}

        for future in concurrent.futures.as_completed(future_to_user):
            username = future_to_user[future]
            try:
                user_data[username] = future.result()
            except Exception as e:
                user_data[username] = {"location": "Error", "email": "Error"}
                print(f"❌ Error fetching data for {username}: {e}")

    #  Final cache save
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(user_data, f)

    # Separate users by country
    sweden_authors = {}
    uk_authors = {}

    for index, row in df.iterrows():
        repo = row["Repository"]
        time_frame = row["Time Frame"]
        username = row["Username"]

        user_info = user_data.get(username, {"location": "Unknown", "email": "Unknown"})
        location = user_info["location"]
        email = user_info["email"]

        if location is None:
            location = "Unknown"
        if email is None:
            email = "Unknown"

         # ✅ Check location OR email domain for Sweden
        if any(keyword in location for keyword in sweden_keywords) or email.endswith(".se"):
            if repo not in sweden_authors:
                sweden_authors[repo] = []
            sweden_authors[repo].append((time_frame, username, location, email))

        # ✅ Check location OR email domain for the UK
        if any(keyword in location for keyword in uk_keywords):
            if repo not in uk_authors:
                uk_authors[repo] = []
            uk_authors[repo].append((time_frame, username, location, email))

    # Save results for Sweden (in current directory)
    for repo, authors in sweden_authors.items():
        output_file = f"{repo}_authors_sweden.csv"
        df_sweden = pd.DataFrame(authors, columns=["Time Frame", "Username", "Location", "Email"])
        df_sweden.to_csv(output_file, index=False)
        print(f"✅ Saved Sweden authors for {repo} to {output_file}")

    # Save results for UK (in current directory)
    for repo, authors in uk_authors.items():
        output_file = f"{repo}_authors_uk.csv"
        df_uk = pd.DataFrame(authors, columns=["Time Frame", "Username", "Location", "Email"])
        df_uk.to_csv(output_file, index=False)
        print(f"✅ Saved UK authors for {repo} to {output_file}")

else:
    print(f"❌ File {input_file} not found!")
