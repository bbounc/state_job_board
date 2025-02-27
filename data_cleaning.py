import pandas as pd

def remove_duplicate_links_and_titles(input_file="all_jobs.csv", output_file="cleaned_data.csv"):
    """Removes duplicate job links and job titles from the input CSV file and saves the cleaned data."""
    # Read the CSV into a DataFrame
    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        print(f"❌ Error reading the CSV file: {e}")
        return
    
    # Check if the necessary columns exist
    if 'Job Link' not in df.columns:
        print("❌ 'Job Link' column not found in the CSV!")
        return
    if 'Job Title' not in df.columns:
        print("❌ 'Job Title' column not found in the CSV!")
        return

    # Normalize links by removing query parameters
    df['Normalized Link'] = df['Job Link'].apply(lambda x: x.split('?')[0])

    # Remove duplicates based on the normalized link
    total_rows_before_link_removal = len(df)
    df_cleaned_by_link = df.drop_duplicates(subset=["Normalized Link"], keep="first")
    total_rows_after_link_removal = len(df_cleaned_by_link)
    removed_rows_by_link = total_rows_before_link_removal - total_rows_after_link_removal

    # Normalize job titles to lowercase and remove leading/trailing spaces for consistent comparison
    df_cleaned_by_link['Normalized Title'] = df_cleaned_by_link['Job Title'].apply(lambda x: x.strip().lower())

    # Remove duplicates based on the normalized title
    total_rows_before_title_removal = len(df_cleaned_by_link)
    df_cleaned_final = df_cleaned_by_link.drop_duplicates(subset=["Normalized Title"], keep="first")
    total_rows_after_title_removal = len(df_cleaned_final)
    removed_rows_by_title = total_rows_before_title_removal - total_rows_after_title_removal

    # Save the cleaned DataFrame to a new CSV (cleaned_data.csv)
    try:
        df_cleaned_final.drop(columns=["Normalized Link", "Normalized Title"], inplace=True)  # Drop helper columns
        df_cleaned_final.to_csv(output_file, index=False)
        print(f"✅ Duplicates removed. {removed_rows_by_link} rows were removed based on job links.")
        print(f"✅ {removed_rows_by_title} rows were removed based on job titles.")
        print(f"Cleaned data saved to {output_file}.")
    except Exception as e:
        print(f"❌ Error saving the cleaned CSV file: {e}")

if __name__ == "__main__":
    remove_duplicate_links_and_titles()  # The output file will be cleaned_data.csv
