import requests
from bs4 import BeautifulSoup
import csv
import re  # For extracting city and state

# Define the base URL with a placeholder for the keyword
BASE_URL = "https://workforindiana.in.gov/search/?searchby=location&createNewAlert=false&q={KEYWORD}&locationsearch=&geolocation=&optionsFacetsDD_customfield3=&optionsFacetsDD_city=&optionsFacetsDD_customfield1="

# Ask for a keyword
keyword = input("What keyword would you like to find: ").strip()  # Strip to remove unwanted spaces

# User-Agent to mimic a real browser request
HEADERS = {"User-Agent": "Mozilla/5.0"}

# Construct the URL with the keyword
url = BASE_URL.replace("{KEYWORD}", keyword)
response = requests.get(url, headers=HEADERS)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, "html.parser")
    job_rows = soup.find_all("tr", class_="data-row")  # Locate job rows

    # Define the CSV file name based on the keyword
    csv_filename = f"{keyword}_jobs.csv"

    # Open a CSV file for writing
    with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        
        # Write the header row
        writer.writerow(["Job Title", "Job Link", "Location", "Salary"])

        for job in job_rows:
            # Extract job title
            title_tag = job.find("a", class_="jobTitle-link")
            title = title_tag.text.strip() if title_tag else "No Title"
            link = "https://workforindiana.in.gov" + title_tag["href"] if title_tag else "#"

            # Extract and format job location
            location_tag = job.find("span", class_="jobLocation")
            full_location = location_tag.text.strip() if location_tag else "Location Not Found"
            
            # Extract "City, State" using regex
            match = re.search(r"([\w\s]+),\s([A-Z]{2})", full_location)
            location = f"{match.group(1)}, {match.group(2)}" if match else "Location Not Found"

            # Extract salary
            salary_tag = job.find("span", class_="jobFacility")  # Based on the salary class from HTML
            salary = salary_tag.text.strip() if salary_tag else "Salary Not Provided"

            # Write data to CSV
            writer.writerow([title, link, location, salary])

    print(f"✅ Job data saved to '{csv_filename}' and can be opened in Excel.")

else:
    print(f"❌ Failed to retrieve jobs for keyword: {keyword}")
