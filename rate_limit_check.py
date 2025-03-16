import requests
import os
from dotenv import load_dotenv

# Load env
load_dotenv()
TOKEN = os.getenv("GITHUB_TOKEN")

# Rate Limit URL
URL = "https://api.github.com/rate_limit"

# Set headers
HEADERS = {"Authorization": f"token {TOKEN}"} if TOKEN else {}

# Fetch data
response = requests.get(URL, headers=HEADERS)

if response.status_code == 200:
    data = response.json()
    print("GitHub API Rate Limit:")
    print(f"  - Core Requests: {data['rate']['remaining']} remaining / {data['rate']['limit']} total")
    print(f"  - Reset Time: {data['rate']['reset']} (Unix timestamp)")
else:
    print(f"Failed to fetch rate limit: {response.status_code} - {response.text}")
