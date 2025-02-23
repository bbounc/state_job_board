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

BASE_URL = "https://careers.georgia.gov/jobs/search/36532760/page"
MAX_PAGE = 125  # Last valid page before looping back
page_num = 1
job_links = []
csv_filename = "ga_job_links.csv"

while page_num <= MAX_PAGE:
    if page_num % 50 == 0:  # Restart driver every 50 pages to prevent memory issues
        print(f"Restarting driver at page {page_num}...")
        driver.quit()
        driver = create_driver()

    url = f"{BASE_URL}{page_num}"
    print(f"Scraping page {page_num}: {url}")
    driver.get(url)

    try:
        # Wait for job listings to appear or detect if the page is empty
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a.job_link.font_bold'))
        )
    except Exception:
        print(f"No job listings found on page {page_num}. Stopping.")
        break  # Stop if the page has no job listings

    # Extract job links
    job_elements = driver.find_elements(By.CSS_SELECTOR, 'a.job_link.font_bold')

    if not job_elements:
        print(f"No job elements found on page {page_num}. Stopping.")
        break  # Stop if no jobs are found

    for job in job_elements:
        link = job.get_attribute("href")
        if link and link not in job_links:
            job_links.append([link])
            print(f"Found job: {link}")

    page_num += 1
    time.sleep(2)  # Prevent bot detection

# Save job links to CSV
with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Job Link"])
    writer.writerows(job_links)

print(f"Total jobs scraped: {len(job_links)}")
print(f"Job links saved to {csv_filename}")

driver.quit()
