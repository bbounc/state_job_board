import requests
from bs4 import BeautifulSoup
import re
import time

def remove_non_ascii(text):
    """Return only ASCII characters from the given text."""
    return ''.join(c for c in text if ord(c) < 128)

def scrape_IN(keywords):
    BASE_URL = (
        "https://workforindiana.in.gov/search/"
        "?q={KEYWORD}"
        "&searchby=location"
        "&d=10"
    )
    HEADERS = {"User-Agent": "Mozilla/5.0"}
    job_listings = []
    unique_jobs = set()

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

                title = title_tag.text.strip()
                link = "https://workforindiana.in.gov" + title_tag["href"]

                # Extract basic info from listing
                location_tag = job.find("span", class_="jobLocation")
                full_location = location_tag.text.strip() if location_tag else "Location Not Found"
                loc_match = re.search(r"([\w\s]+),\s([A-Z]{2})", full_location)
                location = f"{loc_match.group(1).strip()}, {loc_match.group(2)}" if loc_match else "Location Not Found"

                salary_tag = job.find("span", class_="jobFacility")
                salary = salary_tag.text.strip() if salary_tag else "Salary Not Provided"

                # Avoid duplicates
                job_id = (title, link)
                if job_id in unique_jobs:
                    continue
                unique_jobs.add(job_id)

                # Visit the individual job page to extract the department text
                department_text = "Department not found"
                try:
                    detail_resp = requests.get(link, headers=HEADERS)
                    raw_detail = detail_resp.content.decode("utf-8", errors="ignore")
                    fixed_detail = remove_non_ascii(raw_detail)
                    detail_soup = BeautifulSoup(fixed_detail, "html.parser")
                    # Try <span class="jobdescription">, fallback to <div class="jobdescription">
                    desc_span = detail_soup.find("span", class_="jobdescription")
                    if not desc_span:
                        desc_span = detail_soup.find("div", class_="jobdescription")

                    if desc_span:
                        # Look for a <u> tag whose text contains "about" (case-insensitive)
                        about_u = desc_span.find("u", string=lambda s: s and "about".lower() in s.lower())
                        if about_u:
                            dept_raw = about_u.get_text(strip=True)
                            # Remove a leading "about" or "about the" (case-insensitive)
                            department_text = re.sub(r"(?i)^about(?: the)?\s+", "", dept_raw).rstrip(" :;,-")
                            # Remove any non-ASCII characters (if any remain)
                            department_text = remove_non_ascii(department_text)
                    else:
                        print("No jobdescription element found on detail page:", link)
                except Exception as e:
                    department_text = f"Error: {e}"

                job_listing = {
                    "Job Title": title,
                    "Location": location,
                    "Department": department_text,
                    "Salary": salary,
                    "Description": None,  # Not provided by this site
                    "Application Deadline": None,  # Not provided by this site
                    "Link": link
                }
                job_listings.append(job_listing)

            startrow += 25
            time.sleep(1)  # optional short delay

    return job_listings