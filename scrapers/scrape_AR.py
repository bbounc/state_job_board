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

BASE_URL = "https://arcareers.arkansas.gov/search/?q=&sortColumn=referencedate&sortDirection=desc&searchby=location&d=51&startrow="
page_num = 0
job_links = []
csv_filename = "ar_job_links.csv"
link_selector = 'a.jobTitle-link'
stop_selector = 'span.attention.securitySearchString'  # The element indicating no jobs left

while True:
    if page_num % 50 == 0:  # Restart driver every 50 pages to prevent memory issues
        print(f"Restarting driver at page {page_num}...")
        driver.quit()
        driver = create_driver()

    url = f"{BASE_URL}{page_num}"
    print(f"Scraping: {url}")  # Debugging: see current page
    driver.get(url)

    try:
        # Wait for the page to load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Check if the stop condition element is present
        if driver.find_elements(By.CSS_SELECTOR, stop_selector):
            print(f"Stop condition found at page {page_num}. Stopping scraper.")
            break

        # Wait for job links if jobs exist
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, link_selector))
        )
    
    except Exception as e:
        print(f"Error or last page reached at {page_num}: {e}")
        break

    # Extract job links
    job_elements = driver.find_elements(By.CSS_SELECTOR, link_selector)

    if not job_elements:  # If no jobs are found, stop scraping
        print(f"No jobs found at page {page_num}. Stopping scraper.")
        break

    for job in job_elements:
        link = job.get_attribute("href")
        if link:
            job_links.append([link])
            print(f"Found job: {link}")

    page_num += 50
    time.sleep(2)  # Avoid bot detection

# Save job links to CSV
with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Job Link"])
    writer.writerows(job_links)

print(f"Total jobs scraped: {len(job_links)}")
print(f"Job links saved to {csv_filename}")

driver.quit()
