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

BASE_URL = "https://www.jobapscloud.com/MD/"
csv_filename = "md_job_links.csv"
job_links = []

print(f"Scraping: {BASE_URL}")
driver.get(BASE_URL)

while True:
    try:
        # Wait for job links to appear
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a.JobTitle'))
        )

        # Extract job links
        job_elements = driver.find_elements(By.CSS_SELECTOR, 'a.JobTitle')
        for job in job_elements:
            link = job.get_attribute("href")
            if link and link not in job_links:
                job_links.append([link])
                print(f"Found job: {link}")

        # Find and click "Next" button
        try:
            next_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.next'))  # Adjust selector if needed
            )
            next_button.click()
            print("Clicked 'Next' button.")
            time.sleep(3)  # Allow page to load
        except:
            print("No more pages. Stopping.")
            break  # Exit loop if "Next" button isn't found

    except Exception as e:
        print(f"Error encountered: {e}")
        break

# Save job links to CSV
with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Job Link"])
    writer.writerows(job_links)

print(f"Total jobs scraped: {len(job_links)}")
print(f"Job links saved to {csv_filename}")

driver.quit()
