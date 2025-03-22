import numpy as np
import pandas as pd
import os

repo_list = ['electron','freecodecamp','kubernetes', 'n8n', 'pytorch', 'react', 'superset', 'tensorflow', 'vscode', 'vue', 'youtube']

authors = []

if __name__ == '__main__':
    i = 0
    while i < len(repo_list):
        name = repo_list[i]
        try:
            # Load commit data for different time periods
            pre_pandemic = pd.read_csv(f'{name}/{name}_results/commits_2018_2019_{name}.csv')
            pandemic = pd.read_csv(f'{name}/{name}_results/commits_2020_2022_{name}.csv')
            post_pandemic = pd.read_csv(f'{name}/{name}_results/commits_2022_2024_{name}.csv')

            # Load author data
            curr_authors = pd.read_csv(f'{name}/{name}_authors/{name}_authors_uk.csv')

            # Add repository information to the authors dataframe
            curr_authors['repository'] = name
            
                    
            # Then normalize the author names
            pre_pandemic['Username'] = pre_pandemic['Username'].str.lower().str.strip() 
            pandemic['Username'] = pandemic['Username'].str.lower().str.strip()
            post_pandemic['Username'] = post_pandemic['Username'].str.lower().str.strip()
            curr_authors['Username'] = curr_authors['Username'].str.lower().str.strip()
            
            # Count pre-pandemic commits
            pre_commit_counts = pre_pandemic['Username'].value_counts().reset_index()
            pre_commit_counts.columns = ['Username', 'pre_pandemic_commits']
            
            # Count pandemic commits
            pandemic_commit_counts = pandemic['Username'].value_counts().reset_index()
            pandemic_commit_counts.columns = ['Username', 'pandemic_commits']
            
            # Count post-pandemic commits
            post_commit_counts = post_pandemic['Username'].value_counts().reset_index()
            post_commit_counts.columns = ['Username', 'post_pandemic_commits']
            
            # Merge commit counts with author data
            merged_authors = curr_authors.copy()
            merged_authors = merged_authors.merge(pre_commit_counts, on='Username', how='left')
            merged_authors = merged_authors.merge(pandemic_commit_counts, on='Username', how='left')
            merged_authors = merged_authors.merge(post_commit_counts, on='Username', how='left')
            
            # Fill NaN values with 0 (authors with no commits in a period)
            merged_authors['pre_pandemic_commits'] = merged_authors['pre_pandemic_commits'].fillna(0).astype(int)
            merged_authors['pandemic_commits'] = merged_authors['pandemic_commits'].fillna(0).astype(int)
            merged_authors['post_pandemic_commits'] = merged_authors['post_pandemic_commits'].fillna(0).astype(int)
            
            # Calculate total commits
            merged_authors['total_commits'] = (
                merged_authors['pre_pandemic_commits'] + 
                merged_authors['pandemic_commits'] + 
                merged_authors['post_pandemic_commits']
            )
            
            # Debug information
            zero_commit_authors = merged_authors[merged_authors['total_commits'] == 0]
            if len(zero_commit_authors) > 0:
                print(f"\nRepository: {name}")
                print(f"  Found {len(zero_commit_authors)} authors with zero commits in our time periods")
                print("  This might indicate authors who committed outside our studied time periods")
                print("  or name formatting inconsistencies between commits and author lists")
                print("  Sample of zero-commit authors:", zero_commit_authors['Author'].iloc[:5].tolist())
            
            # Include all authors regardless of commit count
            authors.append(merged_authors)
            
            # Print repository summary
            print(f"\nRepository: {name}")
            print(f"  Total authors: {len(merged_authors)}")
            print(f"  Authors with commits in our time periods: {len(merged_authors[merged_authors['total_commits'] > 0])}")
            print(f"  Total commits: {merged_authors['total_commits'].sum()}")
            
            i += 1
            
        except Exception as e:
            print(f"Error processing repository {name}: {str(e)}")
            i += 1
    
    # Combine all authors into a single dataframe
    if authors:
        all_authors = pd.concat(authors, ignore_index=True)
        print("\n=== SUMMARY ===")
        print(f"Total authors across all repositories: {len(all_authors)}")
        print(f"Authors with commits in our time periods: {len(all_authors[all_authors['total_commits'] > 0])}")
        print(f"Total commits: {all_authors['total_commits'].sum()}")
        
        # Save the combined authors data to a CSV
        output_path = "all_authors_with_commits.csv"
        all_authors.to_csv(output_path, index=False)
        print(f"Saved all authors to {output_path}")
        
        # Filter for authors with more than 1 commit
        filtered_authors = all_authors[all_authors['total_commits'] > 1]
        print(f"\n=== FILTERED SUMMARY ===")
        print(f"Total authors with more than 1 commit: {len(filtered_authors)}")
        print(f"Total commits from these authors: {filtered_authors['total_commits'].sum()}")
        
        # Create a new column 'primary_timeframe' to identify when each author was most active
        conditions = [
            (filtered_authors['pre_pandemic_commits'] >= filtered_authors['pandemic_commits']) & 
            (filtered_authors['pre_pandemic_commits'] >= filtered_authors['post_pandemic_commits']),
            
            (filtered_authors['pandemic_commits'] >= filtered_authors['pre_pandemic_commits']) & 
            (filtered_authors['pandemic_commits'] >= filtered_authors['post_pandemic_commits']),
            
            (filtered_authors['post_pandemic_commits'] >= filtered_authors['pre_pandemic_commits']) & 
            (filtered_authors['post_pandemic_commits'] >= filtered_authors['pandemic_commits'])
        ]
        choices = ['2018_2019', '2020_2022', '2022_2024']
        filtered_authors['primary_timeframe'] = np.select(conditions, choices, default='2020_2022')
        
        # Sort by timeframe (ascending)
        filtered_authors = filtered_authors.sort_values(by='primary_timeframe')
        
        # Save the filtered and sorted authors to a CSV
        filtered_output_path = "filtered_authors_by_timeframe.csv"
        filtered_authors.to_csv(filtered_output_path, index=False)
        print(f"Saved filtered authors (>1 commit) ordered by timeframe to {filtered_output_path}")
        
        # Print summary by timeframe
        timeframe_counts = filtered_authors['primary_timeframe'].value_counts().sort_index()
        print("\nAuthors by primary timeframe:")
        for timeframe, count in timeframe_counts.items():
            print(f"  {timeframe}: {count} authors")
    else:
        print("No authors processed")



