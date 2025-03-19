import os
import pandas as pd

repo_folders = {
    "kubernetes": "kubernetes_results",
    "tensorflow": "tensorflow_results",
}

time_frames = [
    ("2018-01-01T00:00:00Z", "2019-12-31T23:59:59Z", "2018_2019"),
    ("2020-01-01T00:00:00Z", "2022-06-30T23:59:59Z", "2020_2022"),
    ("2022-06-01T00:00:00Z", "2024-06-30T23:59:59Z", "2022_2024"),
]

unique_users = {}

# Loop through each repo based on each timeframe
for repo, folder in repo_folders.items():
    for since, until, label in time_frames:
        filename = os.path.join(folder, f"commits_{label}_{repo}.csv")

        if os.path.exists(filename):
            df = pd.read_csv(filename)

            # Check if "Username" column exists
            if "Username" in df.columns:
                users = df["Username"].dropna().drop_duplicates()
                users_list = list(users) 

                if users_list:
                    unique_users[(repo, label)] = users_list
                    print(f"✅ Extracted {len(users_list)} unique users from {filename}")
                else:
                    print(f"⚠️ No users found in {filename}")
            else:
                print(f"❌ Required column 'Username' not found in {filename}")
        else:
            print(f"❌ File not found: {filename}")

# Save results 
output_file = "commit_users_3.csv"
with open(output_file, "w", newline="", encoding="utf-8") as file:
    file.write("Repository,Time Frame,Username\n")
    for (repo, label), users in unique_users.items():
        for username in users:
            file.write(f"{repo},{label},{username}\n")

print(f"✅ Saved unique commit users to {output_file}")
