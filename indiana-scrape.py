import requests
from bs4 import BeautifulSoup
import csv

# Define the base URL with a placeholder for the keyword
BASE_URL = "https://workforindiana.in.gov/search/?searchby=location&createNewAlert=false&q={KEYWORD}&locationsearch=&geolocation=&optionsFacetsDD_customfield3=&optionsFacetsDD_city=&optionsFacetsDD_customfield1="

# Ask for keywords
keywords = input("Enter keywords separated by commas: ").strip().split(',')

# User-Agent to mimic a real browser request
HEADERS = {"User-Agent": "Mozilla/5.0"}

# Open CSV file for writing
csv_filename = "jobs.csv"
unique_jobs = set()  # Set to track unique job postings

with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)

    # Write header row (excluding the keyword column)
    writer.writerow(["Title", "Link", "Location", "Minimum Salary"])

    for keyword in keywords:
        keyword = keyword.strip()  # Remove leading/trailing spaces
        if not keyword:
            continue  # Skip empty keywords

        # Construct the URL with the keyword
        url = BASE_URL.format(KEYWORD=keyword)
        response = requests.get(url, headers=HEADERS)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            job_rows = soup.find_all("tr", class_="data-row")  # Locate job rows

            if not job_rows:
                print(f"No jobs found for keyword: {keyword}")
                continue  # Skip to the next keyword

            for job in job_rows:
                # Extract job title
                title_tag = job.find("a", class_="jobTitle-link")
                title = title_tag.text.strip() if title_tag else "No Title"
                link = "https://workforindiana.in.gov" + title_tag["href"] if title_tag else "#"

                # Extract job location
                location_tag = job.find("span", class_="jobLocation")
                location = location_tag.text.strip() if location_tag else "Location Not Found"

                # Extract salary
                salary_tag = job.find("span", class_="jobFacility")  # Adjust class if incorrect
                salary = salary_tag.text.strip() if salary_tag else "Salary Not Provided"

                # Create a unique identifier (title + link) to remove duplicates
                job_id = (title, link)

                if job_id not in unique_jobs:
                    unique_jobs.add(job_id)
                    writer.writerow([title, link, location, salary])

        else:
            print(f"❌ Failed to retrieve jobs for keyword: {keyword}. HTTP Status: {response.status_code}")

print(f"\n✅ Job data successfully saved to {csv_filename} (duplicates removed)")

