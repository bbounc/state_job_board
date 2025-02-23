import csv
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

def create_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode (no GUI)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def start_scraping():
    driver = create_driver()
    BASE_URL = "https://calcareers.ca.gov/CalHRPublic/Search/JobSearchResults.aspx#empty"
    csv_filename = "ca_job_links.csv"
    job_links = []

    print(f"Scraping: {BASE_URL}")
    driver.get(BASE_URL)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a[id^="cphMainContent_rptResults_hlViewJobPosting_"]'))
        )

        page = 1  # Start at page 1

        while True:
            print(f"Scraping page {page}...")

            # Extract job links
            job_elements = driver.find_elements(By.CSS_SELECTOR, 'a[id^="cphMainContent_rptResults_hlViewJobPosting_"]')
            for job in job_elements:
                link = job.get_attribute("href")
                if link and [link] not in job_links:  # Avoid duplicate links
                    job_links.append([link])
                    print(f"Found job: {link}")

            # Find the pagination button for the next page
            try:
                next_page = driver.find_element(By.XPATH, f"//a[text()='{page + 1}']")
                ActionChains(driver).move_to_element(next_page).perform()
                next_page.click()
                time.sleep(3)  # Allow page to load
                page += 1  # Increment page number

            except Exception:
                print("No more pages to scrape.")
                break  # Stop when there are no more pages

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Save job links to CSV
        if job_links:
            with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["Job Link"])
                writer.writerows(job_links)
            print(f"Total jobs scraped: {len(job_links)}")
            print(f"Job links saved to {csv_filename}")
        else:
            print("No job links found to save.")

        driver.quit()

try:
    start_scraping()
except Exception as e:
    print(f"Error occurred: {e}")
    print("Restarting scraping session...")
    start_scraping()
