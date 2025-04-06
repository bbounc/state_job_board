import csv
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

# Function to create a new WebDriver session
def create_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode (no GUI)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Function to save job links to CSV
def save_to_csv(filename, data):
    if data:
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Job Link"])
            writer.writerows(data)
        print(f"Total jobs scraped: {len(data)}")
        print(f"Job links saved to {filename}")
    else:
        print("No job links found to save.")

# Start WebDriver session
def start_scraping():
    driver = create_driver()

    # URL of the job listings page
    BASE_URL = "https://statejobs.ny.gov/public/vacancyTable.cfm?searchResults=Yes&Keywords=&title=&JurisClassID=&AgID=&isnyhelp=&minDate=&maxDate=&employmentType=&gradeCompareType=GT&grade=&SalMin=" 
    csv_filename = "ny_job_links.csv"
    job_links = []
    next_click_count = 0  # Counter for Next button clicks

    print(f"Scraping: {BASE_URL}")
    driver.get(BASE_URL)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="vacancyDetailsView.cfm?id="]'))
        )

        while True:
            print("Extracting job links...")

            # Extract job links
            job_elements = driver.find_elements(By.CSS_SELECTOR, 'a[href*="vacancyDetailsView.cfm?id="]')
            new_links = [job.get_attribute("href") for job in job_elements if job.get_attribute("href")]
            unique_links = [link for link in new_links if [link] not in job_links]

            if unique_links:
                job_links.extend([[link] for link in unique_links])
                print(f"Found {len(unique_links)} new jobs.")
            else:
                print("No new jobs found. Stopping pagination.")
                break  # Stop if no new jobs appear (prevents looping on last page)

            # Attempt to find and click the "Next" button
            try:
                next_button = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'button.dt-paging-button.next'))
                )

                # Check if "Next" button is disabled
                if "disabled" in next_button.get_attribute("class").lower():
                    print("Next button is disabled. Stopping pagination.")
                    break

                # Scroll to the next button to make sure it's visible
                ActionChains(driver).move_to_element(next_button).perform()
                next_button.click()
                next_click_count += 1  # Increment counter
                print(f"Clicked 'Next' button ({next_click_count} times).")

                # Wait for new job postings to load
                time.sleep(3)  # Allow full page load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="vacancyDetailsView.cfm?id="]'))
                )

            except Exception:
                print("No more pages to scrape or 'Next' button not found.")
                break  # Exit loop when the "Next" button is missing

    except Exception as e:
        print(f"Error during scraping: {e}")

    finally:
        # Save job links to CSV
        save_to_csv(csv_filename, job_links)
        print(f"'Next' button clicked a total of {next_click_count} times.")
        driver.quit()

# Restart the process if session is lost
try:
    start_scraping()
except Exception as e:
    print(f"Error occurred: {e}")
    print("Restarting scraping session...")
    start_scraping()
