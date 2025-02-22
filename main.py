import csv
from scrapers.scrape_IN import scrape_indiana
from scrapers.scrape_DE import scrape_delaware

def main():
    keywords = input("Enter keywords separated by commas: ").split(',')
    
    # Get job listings from both sources
    indiana_jobs = scrape_indiana(keywords)
    de_jobs = scrape_delaware(keywords)
    
    # Combine both job lists
    all_jobs = indiana_jobs + de_jobs

    # Define a unified CSV header
    fieldnames = ["Job Title", "Location", "Department", "Salary", "Description", "Application Deadline", "Link"]
    csv_filename = "combined_jobs.csv"
    with open(csv_filename, mode="w", newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_jobs)

    print(f"✅ Combined job data successfully saved to {csv_filename}")

if __name__ == "__main__":
    main()
