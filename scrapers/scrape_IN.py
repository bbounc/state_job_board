import requests
from bs4 import BeautifulSoup
import time
import csv

def remove_non_ascii(text):
    """Return only ASCII characters from the given text."""
    return ''.join(c for c in text if ord(c) < 128)

def scrape_indiana(keywords):
    BASE_URL = (
        "https://workforindiana.in.gov/search/"
        "?q={KEYWORD}"
        "&searchby=location"
        "&d=10"
    )
    HEADERS = {"User-Agent": "Mozilla/5.0"}
    job_links = set()

    for keyword in keywords:
        keyword = keyword.strip()
        if not keyword:
            continue

        startrow = 0
        while True:
            url = BASE_URL.format(KEYWORD=keyword) + f"&startrow={startrow}"
            print(f"Scraping list page: {url}")
            response = requests.get(url, headers=HEADERS)
            # Decode as UTF-8 and then remove non-ASCII characters
            raw_text = response.content.decode("utf-8", errors="ignore")
            fixed_text = remove_non_ascii(raw_text)
            soup = BeautifulSoup(fixed_text, "html.parser")
            job_rows = soup.find_all("tr", class_="data-row")
            if not job_rows:
                print(f"No more jobs found (startrow={startrow}).")
                break

            for job in job_rows:
                title_tag = job.find("a", class_="jobTitle-link")
                if not title_tag:
                    continue

                link = "https://workforindiana.in.gov" + title_tag["href"]
                job_links.add(link)

            startrow += 25
            time.sleep(1)  # optional short delay

    return job_links

# Function to save job links to CSV
def save_to_csv(filename, job_links):
    if job_links:
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Job Link"])  # Write header
            for link in job_links:
                writer.writerow([link])  # Write each job link
        print(f"Total job links scraped: {len(job_links)}")
        print(f"Job links saved to {filename}")
    else:
        print("No job links to save.")

# Test the scraping function and save results to CSV
keywords = ["developer", "analyst"]  # Example keywords
job_links = scrape_indiana(keywords)

# Save the results to a CSV file
save_to_csv("in_job_links.csv", job_links)
