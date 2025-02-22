import requests
from bs4 import BeautifulSoup
import csv
import re
import time

def scrape_indiana(keywords):
    BASE_URL = (
        "https://workforindiana.in.gov/search/"
        "?q={KEYWORD}"
        "&searchby=location"
        "&d=10"
        # We'll append "&startrow={startrow}" below
    )
    HEADERS = {"User-Agent": "Mozilla/5.0"}

    job_listings = []
    unique_jobs = set()

    for keyword in keywords:
        print("Scraping Indiana jobs for keyword:", keyword)
        keyword = keyword.strip()
        if not keyword:
            continue
        
        startrow = 0  # Start at row 0
        while True:
            # Construct the URL with the current startrow
            url = BASE_URL.format(KEYWORD=keyword) + f"&startrow={startrow}"
            print(f"Scraping: {url}")  # For debugging

            response = requests.get(url, headers=HEADERS)
            if response.status_code != 200:
                print(f"❌ Failed to retrieve jobs for keyword: {keyword} (startrow={startrow}).")
                break

            soup = BeautifulSoup(response.text, "html.parser")
            job_rows = soup.find_all("tr", class_="data-row")

            # If we find no jobs on this page, we're done
            if not job_rows:
                print(f"No more jobs found (startrow={startrow}).")
                break

            # Parse the jobs
            for job in job_rows:
                title_tag = job.find("a", class_="jobTitle-link")
                title = title_tag.text.strip() if title_tag else "No Title"
                link = "https://workforindiana.in.gov" + title_tag["href"] if title_tag else "#"

                location_tag = job.find("span", class_="jobLocation")
                full_location = location_tag.text.strip() if location_tag else "Location Not Found"
                match = re.search(r"([\w\s]+),\s([A-Z]{2})", full_location)
                location = f"{match.group(1).strip()}, {match.group(2)}" if match else "Location Not Found"

                salary_tag = job.find("span", class_="jobFacility")
                salary = salary_tag.text.strip() if salary_tag else "Salary Not Provided"

                job_id = (title, link)
                if job_id not in unique_jobs:
                    unique_jobs.add(job_id)
                    job_listings.append({
                        "Job Title": title,
                        "Link": link,
                        "Location": location,
                        "Salary": salary,
                        "Department": "",       # Not provided by this site
                        "Application Deadline": ""   # Not provided by this site
                    })

            # Increment startrow by 25 for the next page
            startrow += 25

            # Optional: a small delay to be polite and avoid hammering the server
            time.sleep(1)

    return job_listings
