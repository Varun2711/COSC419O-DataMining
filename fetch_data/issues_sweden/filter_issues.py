import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the data
file_path = r'c:\Users\reyha\Desktop\UBC\Term 3 2025\419 o Data Mining\DataMining\COSC419O-DataMining\fetch_data\swedish_contributor_issues.csv'
df = pd.read_csv(file_path)

# Filter issues with Swedish contributor involvement
swedish_involvement = df[(df['Opened by Swedish'] == 'YES') | 
                        (df['Commented by Swedish'] == 'YES')]

# Create separate dataframes for each type of involvement
opened_by_swedish = df[df['Opened by Swedish'] == 'YES']
commented_by_swedish = df[df['Commented by Swedish'] == 'YES']

# Summary statistics
total_issues = len(df)
swedish_involved_issues = len(swedish_involvement)
percent_swedish = (swedish_involved_issues / total_issues) * 100 if total_issues > 0 else 0

print(f"Total issues analyzed: {total_issues}")
print(f"Issues with Swedish involvement: {swedish_involved_issues} ({percent_swedish:.2f}%)")
print(f"Issues opened by Swedish contributors: {len(opened_by_swedish)}")
print(f"Issues commented on by Swedish contributors: {len(commented_by_swedish)}")

# Analyze resolution times
if not swedish_involvement.empty:
    avg_resolution_time = swedish_involvement['Resolution Time (Days)'].mean()
    median_resolution_time = swedish_involvement['Resolution Time (Days)'].median()
    print(f"Average resolution time for Swedish-involved issues: {avg_resolution_time:.2f} days")
    print(f"Median resolution time for Swedish-involved issues: {median_resolution_time:.2f} days")

# Compare with overall resolution times
if not df.empty:
    overall_avg_resolution_time = df['Resolution Time (Days)'].mean()
    overall_median_resolution_time = df['Resolution Time (Days)'].median()
    print(f"Overall average resolution time: {overall_avg_resolution_time:.2f} days")
    print(f"Overall median resolution time: {overall_median_resolution_time:.2f} days")

# Analysis by repository
if not swedish_involvement.empty:
    repo_stats = swedish_involvement.groupby('Repository').agg({
        'Issue Number': 'count',
        'Opened by Swedish': lambda x: (x == 'YES').sum(),
        'Commented by Swedish': lambda x: (x == 'YES').sum(),
        'Resolution Time (Days)': 'mean'
    }).rename(columns={'Issue Number': 'Total Issues'})
    
    print("\nSwedish Contribution by Repository:")
    print(repo_stats)

# Analysis by time frame
if not swedish_involvement.empty:
    time_stats = swedish_involvement.groupby('Time Frame').agg({
        'Issue Number': 'count',
        'Opened by Swedish': lambda x: (x == 'YES').sum(),
        'Commented by Swedish': lambda x: (x == 'YES').sum(),
        'Resolution Time (Days)': 'mean'
    }).rename(columns={'Issue Number': 'Total Issues'})
    
    print("\nSwedish Contribution by Time Frame:")
    print(time_stats)

# Save filtered data to new CSV
swedish_involvement.to_csv('filtered_swedish_issues.csv', index=False)

# Create visualizations
if not swedish_involvement.empty:
    # Plot 2: Resolution time comparison
    plt.figure(figsize=(10, 6))
    data = [
        df[~df.index.isin(swedish_involvement.index)]['Resolution Time (Days)'],
        swedish_involvement['Resolution Time (Days)']
    ]
    plt.boxplot(data, labels=['Non-Swedish Issues', 'Swedish Issues'])
    plt.title('Resolution Time Comparison')
    plt.ylabel('Days to Resolution')
    plt.tight_layout()
    plt.savefig('resolution_time_comparison.png')
    
    # Plot 3: Swedish involvement over time
    plt.figure(figsize=(10, 6))

    # Create a DataFrame with all time frames to ensure 2020_2022 appears even if empty
    all_time_frames = pd.DataFrame({'Time Frame': ['2018_2019', '2020_2022', '2022_2024']})
    time_frame_counts = swedish_involvement['Time Frame'].value_counts().reset_index()
    time_frame_counts.columns = ['Time Frame', 'Count']

    # Merge to ensure all time frames appear
    merged_counts = pd.merge(all_time_frames, time_frame_counts, on='Time Frame', how='left').fillna(0)
    merged_counts = merged_counts.sort_values('Time Frame')

    # Create the plot
    sns.barplot(x='Time Frame', y='Count', data=merged_counts)
    plt.title('Swedish Issues Over Time')
    plt.ylabel('Number of Issues')

    # Add text annotation to highlight the absence in 2020_2022
    if merged_counts[merged_counts['Time Frame'] == '2020_2022']['Count'].values[0] == 0:
        plt.text(1, 0.5, "No Swedish\ninvolvement", ha='center', va='bottom', color='red')

    plt.tight_layout()
    plt.savefig('swedish_issues_over_time.png')

print("\nVisualizations created and saved to current directory.")