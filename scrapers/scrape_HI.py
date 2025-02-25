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

# Start first driver session
driver = create_driver()

BASE_URL = "https://www.governmentjobs.com/careers/hawaii?page="
page_num = 1
job_links = []
csv_filename = "hi_job_links.csv"
search_label = 'a.item-details-link'
no_jobs_selector = "span.attention.securitySearchString"  # Selector for "No jobs available" message

while True:
    if page_num % 50 == 0:  # Restart driver every 50 pages
        print(f"Restarting driver at page {page_num}...")
        driver.quit()
        driver = create_driver()

    url = f"{BASE_URL}{page_num}"
    print(f"Scraping: {url}")  # Debugging: see current page
    driver.get(url)

    try:
        # Wait for the page to load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Check if "no jobs" message appears
        if driver.find_elements(By.CSS_SELECTOR, no_jobs_selector):
            print(f"No jobs found on page {page_num}. Stopping scraper.")
            break

        # Wait for job listings to appear
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, search_label))
        )
    
    except Exception as e:
        print(f"Error or last page reached at {page_num - 1}: {e}")
        break

    # Extract job links
    job_elements = driver.find_elements(By.CSS_SELECTOR, search_label)

    if not job_elements:
        print(f"No job listings found on page {page_num}. Stopping scraper.")
        break

    for job in job_elements:
        link = job.get_attribute("href")
        if link:
            job_links.append([link])
            print(f"Found job: {link}")

    page_num += 1
    time.sleep(2)  # Avoid bot detection

# Save job links to CSV
with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Job Link"])
    writer.writerows(job_links)

print(f"Total jobs scraped: {len(job_links)}")
print(f"Job links saved to {csv_filename}")

driver.quit()
