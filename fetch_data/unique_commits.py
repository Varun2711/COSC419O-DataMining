import os
import pandas as pd

repo_folders = {
    "fcc": "freecodecamp_results",
    "pytorch": "pytorch_results",
    "react": "react_results",
    "vue": "vue_results",
    "vscode": "vscode_results"
}


time_frames = [
    ("2018-01-01T00:00:00Z", "2019-12-31T23:59:59Z", "2018_2019"),
    ("2020-01-01T00:00:00Z", "2022-06-30T23:59:59Z", "2020_2022"),
    ("2022-06-01T00:00:00Z", "2024-06-30T23:59:59Z", "2022_2024"),
]

unique_authors = {}

# Looping through each repo based on each timeframe
for repo,folder in repo_folders.items():
    for since, until, label in time_frames:
        filename = os.path.join(folder, f"commits_{label}_{repo}.csv")
        
        if os.path.exists(filename):
            df = pd.read_csv(filename)

            # Check if "Author" column exists
            if "Author" in df.columns:
                authors = df["Author"].dropna().unique()

                if len(authors) > 0:
                    unique_authors[(repo, label)] = authors
                    print(f"✅ Extracted {len(authors)} unique authors from {filename}")
                else:
                    print(f"⚠️ No authors found in {filename}")
            else:
                print(f"❌ 'Author' column not found in {filename}")
        else:
            print(f"❌ File not found: {filename}")

# Save results
output_file = "commit_authors.csv"
with open(output_file, "w", newline="", encoding="utf-8") as file:
    file.write("Repository,Time Frame,Author\n")
    for (repo, label), authors in unique_authors.items():
        for author in authors:
            file.write(f"{repo},{label},{author}\n")

print(f"✅ Saved unique commit authors to {output_file}")