import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the data files
pr_file_path = r'c:\Users\reyha\Desktop\UBC\Term 3 2025\419 o Data Mining\DataMining\COSC419O-DataMining\fetch_data\swedish_contributor_prs.csv'
users_file_path = r'c:\Users\reyha\Desktop\UBC\Term 3 2025\419 o Data Mining\DataMining\COSC419O-DataMining\fetch_data\repos_sweden_users.csv'

# Load the datasets
pr_df = pd.read_csv(pr_file_path)
users_df = pd.read_csv(users_file_path)

# ---------- ANALYSIS 1: Time Frame Distribution ----------
print("======= TIME FRAME DISTRIBUTION =======")
time_frame_counts = pr_df['Time Frame'].value_counts()
print("All PRs by time frame:")
print(time_frame_counts)

# ---------- ANALYSIS 2: Swedish Contribution by Time Frame ----------
print("\n======= SWEDISH CONTRIBUTION BY TIME FRAME =======")
# Count PRs with Swedish contribution in each time frame
for time_frame in pr_df['Time Frame'].unique():
    swedish_count = pr_df[(pr_df['Time Frame'] == time_frame) & 
                         ((pr_df['Opened by Swedish'] == 'YES') | 
                          (pr_df['Commented by Swedish'] == 'YES') | 
                          (pr_df['Reviewed by Swedish'] == 'YES'))].shape[0]
    
    total_count = pr_df[pr_df['Time Frame'] == time_frame].shape[0]
    
    print(f"{time_frame}: {swedish_count} Swedish contributions out of {total_count} PRs ({swedish_count/total_count*100:.2f}%)")

# ---------- ANALYSIS 3: Swedish Users by Time Frame ----------
print("\n======= SWEDISH USERS BY TIME FRAME =======")
# Count Swedish users in each time frame
for time_frame in users_df['Time Frame'].unique():
    user_count = users_df[users_df['Time Frame'] == time_frame].shape[0]
    print(f"{time_frame}: {user_count} Swedish users identified")

# ---------- ANALYSIS 4: Cross-reference Users with PRs ----------
print("\n======= CROSS-REFERENCE ANALYSIS =======")
# Get all Swedish usernames
all_swedish_usernames = set(users_df['Username'].dropna())

# Find PRs by Swedish users that might have been missed
for time_frame in pr_df['Time Frame'].unique():
    # Get users for this time frame
    time_frame_users = set(users_df[users_df['Time Frame'] == time_frame]['Username'].dropna())
    
    # Find PRs authored by these users
    authored_prs = pr_df[(pr_df['Time Frame'] == time_frame) & 
                        (pr_df['Author'].isin(time_frame_users))]
    
    # Find PRs where Opened by Swedish is YES
    opened_prs = pr_df[(pr_df['Time Frame'] == time_frame) & 
                      (pr_df['Opened by Swedish'] == 'YES')]
    
    print(f"{time_frame}:")
    print(f"  Swedish users in this time frame: {len(time_frame_users)}")
    print(f"  PRs authored by Swedish users: {len(authored_prs)}")
    print(f"  PRs marked as 'Opened by Swedish': {len(opened_prs)}")
    
    # Check for discrepancies
    if len(authored_prs) != len(opened_prs):
        print(f"  ⚠️ DISCREPANCY DETECTED: {len(authored_prs)} PRs authored vs {len(opened_prs)} PRs marked")
        
        # Find the specific discrepancies
        missing_prs = authored_prs[authored_prs['Opened by Swedish'] != 'YES']
        if not missing_prs.empty:
            print(f"  First few PRs authored by Swedish users but not marked as Swedish:")
            print(missing_prs[['Repository', 'PR Number', 'Author', 'PR Title']].head())

# ---------- ANALYSIS 5: Detailed Look at 2020-2022 ----------
print("\n======= DETAILED LOOK AT 2020-2022 =======")
# Get all Swedish users from 2020-2022
swedish_2020_2022_users = set(users_df[users_df['Time Frame'] == '2020_2022']['Username'].dropna())
print(f"Number of Swedish users in 2020-2022: {len(swedish_2020_2022_users)}")

# Check if any of these users appear as authors in any time frame
for time_frame in pr_df['Time Frame'].unique():
    swedish_authors = pr_df[(pr_df['Time Frame'] == time_frame) & 
                           (pr_df['Author'].isin(swedish_2020_2022_users))]
    
    print(f"2020-2022 Swedish users who authored PRs in {time_frame}: {len(swedish_authors)}")
    if len(swedish_authors) > 0:
        print("Sample of these PRs:")
        print(swedish_authors[['Repository', 'PR Number', 'Author', 'PR Title']].head())

# ---------- PLOT: Swedish Contribution Over Time ----------
plt.figure(figsize=(12, 6))
time_frames = sorted(pr_df['Time Frame'].unique())
metrics = ['Opened by Swedish', 'Commented by Swedish', 'Reviewed by Swedish']

data = []
for time_frame in time_frames:
    for metric in metrics:
        count = pr_df[(pr_df['Time Frame'] == time_frame) & 
                     (pr_df[metric] == 'YES')].shape[0]
        data.append({'Time Frame': time_frame, 'Type': metric, 'Count': count})

plot_df = pd.DataFrame(data)
sns.barplot(x='Time Frame', y='Count', hue='Type', data=plot_df)
plt.title('Swedish GitHub Contributions Over Time')
plt.savefig('swedish_contributions_over_time.png')
print("\nPlot saved as 'swedish_contributions_over_time.png'")