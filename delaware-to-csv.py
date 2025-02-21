import requests
from bs4 import BeautifulSoup
import re
import csv


def scrape_DE(keywords):
    # Define the base URL with a placeholder for the keyword
    BASE_URL = "https://www.jobapscloud.com/DE/?Keyword={KEYWORD}&Loc=&DeptNumber=&OccList=&JobType=&KeywordFullText=0&PGList="

    # User-Agent to mimic a real browser request
    HEADERS = {"User-Agent": "Mozilla/5.0"}

    # Initialize an empty list to store job listings
    job_listings = []

    # Loop through each keyword
    for keyword in keywords:
        keyword = keyword.strip()  # Strip any extra spaces
        url = BASE_URL.replace("{KEYWORD}", keyword)
        response = requests.get(url, headers=HEADERS)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Iterate through each job card and extract the information
            tables = soup.find_all("table", class_="JobListing")
            
            for table in tables:
                rows = table.find_all("tr", class_=["even", "odd"])
                
                for row in rows:
                    job_title = row.find("a", class_="JobTitle").text.strip()
                    work_location_full = row.find("td", class_="Locs").text.strip().replace("\n", " ").replace("  ", " ")

                    match = re.search(r",\s([a-zA-Z\s]+),\s([A-Za-z]{2})", work_location_full)
                    if match:
                        city = match.group(1).strip()  # Extract city
                        state = match.group(2).strip()  # Extract state
                        work_location = f"{city}, {state}"  # Combine city and state
                    else:
                        # If regex fails, print the full location for debugging purposes
                        work_location = work_location_full

                    department = row.find_all("td")[2].text.strip()
                    salary = row.find_all("td")[3].text.strip()
                    filing_deadline = row.find_all("td")[4].text.strip()
                    
                    job_listing = {
                        "Job Title": job_title,
                        "Location": work_location,
                        "Department": department,
                        "Salary": salary,
                        "Filing Deadline": filing_deadline,
                    }
                    
                    # Append the job listing dictionary to the job listings list
                    job_listings.append(job_listing)

    # Define CSV file name
    csv_filename = "job_listings_DE.csv"

    # Write to CSV
    with open(csv_filename, mode="w", newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["Job Title", "Location", "Department", "Salary", "Filing Deadline"])
        
        # Write the header (column names)
        writer.writeheader()
        
        # Write the job listings
        writer.writerows(job_listings)

    print(f"Job listings have been written to {csv_filename}")


# Ask for multiple keywords
keywords = input("Enter keywords separated by commas: ").strip().split(',')
scrape_DE(keywords)