import requests
from bs4 import BeautifulSoup
import csv

def scrape_delaware():
    BASE_URL = "https://www.jobapscloud.com/DE/?Keyword=&Loc=&DeptNumber=&OccList=&JobType=&KeywordFullText=0&PGList="
    HEADERS = {"User-Agent": "Mozilla/5.0"}
    job_links = []

    print("Scraping Delaware job listings...")

    # Create a session to maintain cookies and other session data
    session = requests.Session()
    session.headers.update(HEADERS)

    # Start scraping job listings
    response = session.get(BASE_URL)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        tables = soup.find_all("table", class_="JobListing")
        
        for table in tables:
            rows = table.find_all("tr", class_=["even", "odd"])
            for row in rows:
                job_title_tag = row.find("a", class_="JobTitle")
                if job_title_tag:
                    job_link = job_title_tag["href"]
                    # Check if the URL is relative or absolute
                    if job_link.startswith("/DE"):  # Relative URL
                        job_link = "https://www.jobapscloud.com" + job_link
                    elif not job_link.startswith("https://"):  # In case it's malformed
                        job_link = "https://www.jobapscloud.com/DE/" + job_link
                    job_links.append(job_link)
                    print(f"Found job link: {job_link}")
    else:
        print(f"❌ Failed to retrieve DE job listings. HTTP Status: {response.status_code}")

    return job_links


def save_job_links_to_csv(job_links, filename="de_job_links.csv"):
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Job Link"])
        for link in job_links:
            writer.writerow([link])

    print(f"Job links saved to {filename}")


# Main execution
job_links = scrape_delaware()
save_job_links_to_csv(job_links)
