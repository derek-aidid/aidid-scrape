import pandas as pd
import os

# List of CSV files to combine
csv_files = [
    'C:/Users/derek/Downloads/最新新聞_articles.csv',
    'C:/Users/derek/Downloads/房市熱區_articles.csv',
    'C:/Users/derek/Downloads/品味家居_articles.csv',
    'C:/Users/derek/Downloads/案場直擊_articles.csv',
    'C:/Users/derek/Downloads/地產思維_articles.csv',
]

# Initialize an empty list to store DataFrames
dataframes = []

# Loop through each CSV file and read it into a DataFrame
for file in csv_files:
    df = pd.read_csv(file)
    dataframes.append(df)

# Concatenate all DataFrames
combined_df = pd.concat(dataframes, ignore_index=True)

# Save the combined DataFrame to a new CSV file
output_csv_path = 'C:/Users/derek/Downloads/combined_articles.csv'
combined_df.to_csv(output_csv_path, index=False, encoding='utf-8-sig')

print(f"Combined data saved to {output_csv_path}")
