import requests
from bs4 import BeautifulSoup
import re

def scrape_delaware(keywords):
    BASE_URL = "https://www.jobapscloud.com/DE/?Keyword={KEYWORD}&Loc=&DeptNumber=&OccList=&JobType=&KeywordFullText=0&PGList="
    HEADERS = {"User-Agent": "Mozilla/5.0"}
    job_listings = []

    for keyword in keywords:
        print("Scraping Delaware jobs for keyword:", keyword)
        keyword = keyword.strip()
        url = BASE_URL.replace("{KEYWORD}", keyword)
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            tables = soup.find_all("table", class_="JobListing")
            for table in tables:
                rows = table.find_all("tr", class_=["even", "odd"])
                for row in rows:
                    job_title_tag = row.find("a", class_="JobTitle")
                    job_title = job_title_tag.text.strip() if job_title_tag else "No Title"
                    job_link = job_title_tag["href"] if job_title_tag else "#"
                    work_location_full = row.find("td", class_="Locs").text.strip().replace("\n", " ").replace("  ", " ")

                    match = re.search(r",\s([a-zA-Z\s]+),\s([A-Za-z]{2})", work_location_full)
                    if match:
                        city = match.group(1).strip()
                        state = match.group(2).strip()
                        work_location = f"{city}, {state}"
                    else:
                        work_location = work_location_full

                    tds = row.find_all("td")
                    department = tds[2].text.strip() if len(tds) > 2 else ""
                    salary = tds[3].text.strip() if len(tds) > 3 else ""
                    filing_deadline = tds[4].text.strip() if len(tds) > 4 else ""
                    
                    job_listing = {
                        "Job Title": job_title,
                        "Link": job_link,
                        "Location": work_location,
                        "Salary": salary,
                        "Department": department,
                        "Application Deadline": filing_deadline
                    }
                    job_listings.append(job_listing)
        else:
            print(f"❌ Failed to retrieve DE jobs for keyword: {keyword}. HTTP Status: {response.status_code}")
    return job_listings
