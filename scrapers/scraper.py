import csv
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

## This scrapper works when the url has some form of index= that can be iterated through

# Function to create a new WebDriver session
def create_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode (no GUI)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Start first driver session
driver = create_driver()

BASE_URL = "https://work4.illinois.gov/jobtitle.html"
page_num = 1
job_links = []
csv_filename = "va_job_links.csv"

while True:
    if page_num % 50 == 0:  # Restart driver every 50 pages
        print(f"Restarting driver at page {page_num}...")
        driver.quit()
        driver = create_driver()

    url = f"{BASE_URL}{page_num}"
    print(f"Scraping: {url}")  # Debugging: see current page
    driver.get(url)

    try:
        # Wait for job links to appear
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href^="/jobtitle/jobtitledetails.html"][target="_blank"]'))
        )
    except Exception as e:
        print(f"Reached last page at {page_num - 1} or encountered an issue: {e}")
        break

    # Extract job links
    job_elements = driver.find_elements(By.CSS_SELECTOR, 'a[href^="/jobtitle/jobtitledetails.html"][target="_blank"]')

    if not job_elements:
        break  # No jobs found, stop

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
