import csv
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Function to create a WebDriver session
def create_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode (no GUI)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Initialize WebDriver
driver = create_driver()

# Target URL (Job Listings Page)
BASE_URL = "https://www.jobapscloud.com/CT/"
csv_filename = "ct_job_links.csv"
job_links = []

print(f"[DEBUG] Scraping: {BASE_URL}")
driver.get(BASE_URL)

try:
    # Wait for job links to appear
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'a.JobTitle'))
    )
    print("[DEBUG] Job listings detected!")

    # Extract job links
    job_elements = driver.find_elements(By.CSS_SELECTOR, 'a.JobTitle')

    if not job_elements:
        print("[ERROR] No job elements found. Exiting.")
    else:
        for job in job_elements:
            link = job.get_attribute("href")
            if link:
                job_links.append([link])  # Only append the link
                print(f"[DEBUG] Found Job Link: {link}")

except Exception as e:
    print(f"[ERROR] An issue occurred while scraping: {e}")

# Save job links to CSV
if job_links:
    with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Job Link"])  # Only write the "Job Link" header
        writer.writerows(job_links)  # Write the job links

    print(f"[INFO] Total jobs scraped: {len(job_links)}")
    print(f"[INFO] Job links saved to {csv_filename}")
else:
    print("[INFO] No job listings were scraped.")

# Close WebDriver
driver.quit()
