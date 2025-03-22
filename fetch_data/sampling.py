import random
import numpy as np
import pandas as pd

if __name__ == '__main__':
    
    authors = pd.read_csv('filtered_authors_by_timeframe.csv')
    
    # Display the total count and distribution by primary timeframe
    print(f"Total number of authors: {len(authors)}")
    timeframe_counts = authors['primary_timeframe'].value_counts()
    print("Distribution by primary timeframe:")
    print(timeframe_counts)
    
    # Define how many entries to sample from each timeframe
    # You can adjust these numbers based on your requirements
    sample_sizes = {
        '2018_2019': 24,
        '2020_2022': 16,
        '2022_2024': 7,
        # Add other timeframe categories if needed
    }
    
    # Create an empty dataframe to store the combined samples
    combined_sample = pd.DataFrame()
    
    # Sample from each timeframe
    for timeframe, size in sample_sizes.items():
        # Filter authors by timeframe
        timeframe_authors = authors[authors['primary_timeframe'] == timeframe]
        
        # Check if we have enough entries for the requested sample size
        actual_size = min(size, len(timeframe_authors))
        
        if actual_size > 0:
            # Sample randomly from this timeframe
            sample = timeframe_authors.sample(n=actual_size, random_state=42)  # Set random_state for reproducibility
            
            # Add to the combined sample
            combined_sample = pd.concat([combined_sample, sample])
            
            print(f"Sampled {actual_size} authors from {timeframe}")
        else:
            print(f"No authors found for timeframe: {timeframe}")
    
    # Shuffle the combined sample
    combined_sample = combined_sample.sample(frac=1, random_state=42).reset_index(drop=True)
    
    # Save the combined sample to a new CSV file
    combined_sample.to_csv('sampled_authors.csv', index=False)
    
    print(f"Total sampled authors: {len(combined_sample)}")
    print(f"Sample saved to 'sampled_authors.csv'")

