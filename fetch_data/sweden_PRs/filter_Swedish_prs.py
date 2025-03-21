import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the data
file_path = r'c:\Users\reyha\Desktop\UBC\Term 3 2025\419 o Data Mining\DataMining\COSC419O-DataMining\fetch_data\swedish_contributor_prs.csv'
df = pd.read_csv(file_path)

# Filter PRs with Swedish contributor involvement
swedish_involvement = df[(df['Opened by Swedish'] == 'YES') | 
                         (df['Commented by Swedish'] == 'YES') | 
                         (df['Reviewed by Swedish'] == 'YES')]

# Create separate dataframes for each type of involvement
opened_by_swedish = df[df['Opened by Swedish'] == 'YES']
commented_by_swedish = df[df['Commented by Swedish'] == 'YES']
reviewed_by_swedish = df[df['Reviewed by Swedish'] == 'YES']

# Summary statistics
total_prs = len(df)
swedish_involved_prs = len(swedish_involvement)
percent_swedish = (swedish_involved_prs / total_prs) * 100 if total_prs > 0 else 0

print(f"Total PRs analyzed: {total_prs}")
print(f"PRs with Swedish involvement: {swedish_involved_prs} ({percent_swedish:.2f}%)")
print(f"PRs opened by Swedish contributors: {len(opened_by_swedish)}")
print(f"PRs commented on by Swedish contributors: {len(commented_by_swedish)}")
print(f"PRs reviewed by Swedish contributors: {len(reviewed_by_swedish)}")

# Analyze merge times
if not swedish_involvement.empty:
    avg_merge_time = swedish_involvement['Merge Time (Days)'].mean()
    median_merge_time = swedish_involvement['Merge Time (Days)'].median()
    print(f"Average merge time for Swedish-involved PRs: {avg_merge_time:.2f} days")
    print(f"Median merge time for Swedish-involved PRs: {median_merge_time:.2f} days")

# Compare with overall merge times
if not df.empty:
    overall_avg_merge_time = df['Merge Time (Days)'].mean()
    overall_median_merge_time = df['Merge Time (Days)'].median()
    print(f"Overall average merge time: {overall_avg_merge_time:.2f} days")
    print(f"Overall median merge time: {overall_median_merge_time:.2f} days")

# Analysis by repository
if not swedish_involvement.empty:
    repo_stats = swedish_involvement.groupby('Repository').agg({
        'PR Number': 'count',
        'Opened by Swedish': lambda x: (x == 'YES').sum(),
        'Commented by Swedish': lambda x: (x == 'YES').sum(),
        'Reviewed by Swedish': lambda x: (x == 'YES').sum(),
        'Merge Time (Days)': 'mean'
    }).rename(columns={'PR Number': 'Total PRs'})
    
    print("\nSwedish Contribution by Repository:")
    print(repo_stats)

# Analysis by time frame
if not swedish_involvement.empty:
    time_stats = swedish_involvement.groupby('Time Frame').agg({
        'PR Number': 'count',
        'Opened by Swedish': lambda x: (x == 'YES').sum(),
        'Commented by Swedish': lambda x: (x == 'YES').sum(),
        'Reviewed by Swedish': lambda x: (x == 'YES').sum(),
        'Merge Time (Days)': 'mean'
    }).rename(columns={'PR Number': 'Total PRs'})
    
    print("\nSwedish Contribution by Time Frame:")
    print(time_stats)

# Save filtered data to new CSV
swedish_involvement.to_csv('filtered_swedish_prs.csv', index=False)