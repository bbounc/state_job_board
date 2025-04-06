import csv
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Function to create a new WebDriver session
def create_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode (no GUI)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Initialize WebDriver
driver = create_driver()

BASE_URL = "https://www.governmentjobs.com/careers/iowa?page="
page_num = 1
job_links = []
csv_filename = "ia_job_links.csv"

while True:
    url = f"{BASE_URL}{page_num}"
    print(f"[DEBUG] Scraping: {url}")
    driver.get(url)

    try:
        # Wait for job elements to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a.item-details-link'))
        )
        print(f"[DEBUG] Job listings detected on page {page_num}")
    except Exception as e:
        print(f"[ERROR] No jobs found or issue encountered on page {page_num}: {e}")
        break

    # Extract job links
    job_elements = driver.find_elements(By.CSS_SELECTOR, 'a.item-details-link')

    if not job_elements:
        print(f"[INFO] No job listings found on page {page_num}. Stopping.")
        break  # No jobs found, stop

    for job in job_elements:
        link = job.get_attribute("href")
        title = job.text.strip()
        if link:
            job_links.append([title, link])
            print(f"[DEBUG] Found Job: {title} -> {link}")

    page_num += 1
    time.sleep(2)  # Avoid bot detection

# Save job links to CSV
if job_links:
    with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Job Title", "Job Link"])
        writer.writerows(job_links)

    print(f"[INFO] Total jobs scraped: {len(job_links)}")
    print(f"[INFO] Job links saved to {csv_filename}")
else:
    print("[INFO] No job listings were scraped.")

# Close WebDriver
driver.quit()
