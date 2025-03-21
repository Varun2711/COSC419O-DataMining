import aiohttp
import asyncio
import json
import os
import time
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Authorization": f"token {TOKEN}" if TOKEN else "",
    "Accept": "application/vnd.github.v3+json"
}

# Define repositories
repositories = [
    ("vuejs", "vue"),
    ("electron", "electron"),
    ("freeCodeCamp", "freeCodeCamp"),
    ("kubernetes", "kubernetes"),
    ("n8n-io", "n8n"),
    ("pytorch", "pytorch"),
    ("facebook", "react"),
    ("apache", "superset"),
    ("tensorflow", "tensorflow"),
    ("microsoft", "vscode"),
    ("ytdl-org", "youtube-dl"),
]

# Time periods
time_frames = [
    ("2018-01-01T00:00:00Z", "2019-12-31T23:59:59Z", "2018_2019"),
    ("2020-01-01T00:00:00Z", "2022-06-30T23:59:59Z", "2020_2022"),
    ("2022-06-01T00:00:00Z", "2024-06-30T23:59:59Z", "2022_2024"),
]

# Load Swedish users
swedish_users = set()
filename = "repos_sweden_users.csv"
if os.path.exists(filename):
    df = pd.read_csv(filename)
    swedish_users.update(df["Username"].dropna().unique())

print(f"✅ Loaded {len(swedish_users)} unique Swedish contributors.")

# Load cached PR data
cache_file = "cached_prs.json"
if os.path.exists(cache_file):
    with open(cache_file, "r", encoding="utf-8") as f:
        cached_pr_data = json.load(f)
else:
    cached_pr_data = {}

print(f"📁 Loaded {len(cached_pr_data)} cached PR records.")

# Create detailed cache file for individual PRs
detailed_cache_file = "cached_pr_details.json"
if os.path.exists(detailed_cache_file):
    with open(detailed_cache_file, "r", encoding="utf-8") as f:
        cached_pr_details = json.load(f)
else:
    cached_pr_details = {}

print(f"📁 Loaded {len(cached_pr_details)} cached PR details.")

# Rate limit tracking
rate_limit_remaining = 5000
rate_limit_reset_time = 0

async def check_rate_limit(session):
    """Check GitHub API rate limit status"""
    global rate_limit_remaining, rate_limit_reset_time
    
    try:
        async with session.get("https://api.github.com/rate_limit") as response:
            if response.status == 200:
                data = await response.json()
                rate_limit_remaining = data["resources"]["core"]["remaining"]
                rate_limit_reset_time = data["resources"]["core"]["reset"]
                
                print(f"🔄 Rate limit remaining: {rate_limit_remaining}")
                return rate_limit_remaining
            else:
                print(f"⚠️ Failed to check rate limit: {response.status}")
                return 0
    except Exception as e:
        print(f"⚠️ Error checking rate limit: {e}")
        return 0

async def wait_for_rate_limit(session):
    """Wait if rate limit is approaching zero"""
    await check_rate_limit(session)
    
    if rate_limit_remaining < 10:
        current_time = time.time()
        sleep_time = max(rate_limit_reset_time - current_time + 10, 0)
        
        if sleep_time > 0:
            print(f"🚨 Rate limit almost reached! Sleeping for {sleep_time:.1f} seconds")
            await asyncio.sleep(sleep_time)
            await check_rate_limit(session)

async def fetch_prs_for_timeframe(session, owner, repo, since, until, timeframe):
    """Fetch PRs for a specific repository and timeframe"""
    cache_key = f"{owner}_{repo}_{timeframe}"
    
    # Check if we have this data cached
    if cache_key in cached_pr_data:
        print(f"⚡ Using cached data for {owner}/{repo} ({timeframe})")
        return cached_pr_data[cache_key]
    
    print(f"🔍 Fetching PRs for {owner}/{repo} ({timeframe})...")
    
    # Use API date filtering to reduce the number of PRs fetched
    # 'since' parameter filters by updated date, not created date, so we'll still filter in code
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    params = {
        "state": "closed",
        "per_page": 100,
        "sort": "updated",
        "direction": "desc"
    }
    
    all_prs = []
    page = 1
    stop_fetching = False
    
    while not stop_fetching:
        await wait_for_rate_limit(session)
        
        try:
            current_params = {**params, "page": page}
            async with session.get(url, params=current_params) as response:
                if response.status == 200:
                    prs = await response.json()
                    
                    if not prs:
                        break  # No more data
                    
                    # Process PRs and check if we've gone past our time window
                    all_before_timeframe = True
                    
                    for pr in prs:
                        created_at = pr["created_at"]
                        
                        # If PR was created before our time frame, skip it
                        if created_at < since:
                            continue
                            
                        # If PR was created after our time frame, skip it
                        if created_at > until:
                            continue
                            
                        all_before_timeframe = False
                        
                        # Process this PR
                        pr_data = await process_pr(session, owner, repo, pr, timeframe)
                        if pr_data:
                            all_prs.append(pr_data)
                    
                    # If all PRs in this page are before our time frame, we can stop
                    if all_before_timeframe and page > 1:
                        stop_fetching = True
                    else:
                        page += 1
                        
                elif response.status == 403:
                    # Rate limited
                    retry_after = int(response.headers.get("Retry-After", "60"))
                    print(f"🚨 Rate limited! Waiting for {retry_after} seconds...")
                    await asyncio.sleep(retry_after)
                    
                else:
                    print(f"❌ Failed to fetch PRs: {response.status}")
                    break
                    
        except Exception as e:
            print(f"❌ Error fetching PRs: {e}")
            await asyncio.sleep(5)  # Short delay on error
    
    # Cache the results for this timeframe
    cached_pr_data[cache_key] = all_prs
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(cached_pr_data, f)
    
    return all_prs

async def process_pr(session, owner, repo, pr, timeframe):
    """Process a single PR and fetch its details"""
    global cached_pr_details
    
    pr_number = pr["number"]
    author = pr["user"]["login"] if pr["user"] else "ghost"
    created_at = pr["created_at"]
    merged_at = pr["merged_at"]
    
    # Skip PRs that weren't merged
    if not merged_at:
        return None
    
    # Create a cache key for this specific PR
    pr_cache_key = f"{owner}_{repo}_{pr_number}"
    
    # Check if we already have cached data for this PR
    if pr_cache_key in cached_pr_details:
        pr_details = cached_pr_details[pr_cache_key]
        
        # Return formatted data for this PR
        return [
            timeframe,
            repo,
            pr_number,
            pr_details["title"],
            author,
            "YES" if author in swedish_users else "NO",
            pr_details["comment_count"],
            "YES" if pr_details["commented_by_swedish"] else "NO",
            pr_details["review_count"],
            "YES" if pr_details["reviewed_by_swedish"] else "NO",
            pr_details["merge_time"]
        ]
    
    # Fetch PR details using GraphQL for efficiency (gets comments and reviews in one request)
    await wait_for_rate_limit(session)
    
    try:
        # Use the REST API to fetch comments and reviews
        comments_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
        reviews_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        
        # Fetch comments
        commenters = set()
        async with session.get(comments_url) as comments_response:
            if comments_response.status == 200:
                comments = await comments_response.json()
                for comment in comments:
                    if comment.get("user") and comment["user"].get("login"):
                        commenters.add(comment["user"]["login"])
        
        # Fetch reviews
        reviewers = set()
        async with session.get(reviews_url) as reviews_response:
            if reviews_response.status == 200:
                reviews = await reviews_response.json()
                for review in reviews:
                    if review.get("user") and review["user"].get("login"):
                        reviewers.add(review["user"]["login"])
        
        # Check if any Swedish user commented or reviewed
        commented_by_swedish = any(user in swedish_users for user in commenters)
        reviewed_by_swedish = any(user in swedish_users for user in reviewers)
        
        # Calculate time to merge
        if merged_at:
            created_time = pd.to_datetime(created_at)
            merged_time = pd.to_datetime(merged_at)
            merge_time = (merged_time - created_time).days
        else:
            merge_time = "Not Merged"
        
        # Store PR details in cache
        pr_details = {
            "title": pr["title"],
            "comment_count": len(commenters),
            "commented_by_swedish": commented_by_swedish,
            "review_count": len(reviewers),
            "reviewed_by_swedish": reviewed_by_swedish,
            "merge_time": merge_time
        }
        
        cached_pr_details[pr_cache_key] = pr_details
        
        # Periodically save the cached details
        if len(cached_pr_details) % 10 == 0:
            with open(detailed_cache_file, "w", encoding="utf-8") as f:
                json.dump(cached_pr_details, f)
        
        # Return formatted data for this PR
        return [
            timeframe,
            repo,
            pr_number,
            pr["title"],
            author,
            "YES" if author in swedish_users else "NO",
            len(commenters),
            "YES" if commented_by_swedish else "NO",
            len(reviewers),
            "YES" if reviewed_by_swedish else "NO",
            merge_time
        ]
        
    except Exception as e:
        print(f"❌ Error processing PR {pr_number}: {e}")
        return None

async def main():
    """Main function to orchestrate the fetching and processing of data"""
    pr_data = []
    total_tasks = len(repositories) * len(time_frames)
    completed_tasks = 0
    
    # Create async session
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        # Check rate limit before starting
        await check_rate_limit(session)
        
        # Process repositories in parallel with concurrency control
        # Use a semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(3)  # Limit to 3 concurrent repositories
        
        async def process_with_semaphore(owner, repo, since, until, timeframe):
            async with semaphore:
                return await fetch_prs_for_timeframe(session, owner, repo, since, until, timeframe)
        
        # Create tasks
        tasks = []
        for owner, repo in repositories:
            for since, until, timeframe in time_frames:
                task = process_with_semaphore(owner, repo, since, until, timeframe)
                tasks.append(task)
        
        # Execute tasks with progress tracking
        for i, task in enumerate(asyncio.as_completed(tasks)):
            try:
                repo_data = await task
                pr_data.extend(repo_data)
                completed_tasks += 1
                progress = (completed_tasks / total_tasks) * 100
                print(f"⏳ Progress: {progress:.2f}% ({completed_tasks}/{total_tasks} tasks completed)")
            except Exception as e:
                print(f"❌ Task error: {e}")
    
    # Save the final cached PR details
    with open(detailed_cache_file, "w", encoding="utf-8") as f:
        json.dump(cached_pr_details, f)
    
    # Convert to DataFrame
    df_prs = pd.DataFrame(pr_data, columns=[
        "Time Frame", "Repository", "PR Number", "PR Title", "Author",
        "Opened by Swedish", "Total Comments", "Commented by Swedish",
        "Total Reviews", "Reviewed by Swedish", "Merge Time (Days)"
    ])
    
    # Save the results to CSV
    output_file = "swedish_contributor_prs.csv"
    df_prs.to_csv(output_file, index=False)
    
    print(f"\n✅ Data saved to {output_file}")
    print(f"📊 Total PRs analyzed: {len(df_prs)}")

# Run the async main function
if __name__ == "__main__":
    start_time = time.time()
    print(f"🚀 Script started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        asyncio.run(main())
        
        end_time = time.time()
        duration = end_time - start_time
        print(f"✨ Script completed in {duration:.2f} seconds ({duration/60:.2f} minutes)")
        
    except KeyboardInterrupt:
        print("\n⛔ Script interrupted by user")
        
    except Exception as e:
        print(f"\n💥 Script error: {e}")