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
    BASE_URL = "https://kypersonnelcabinet.csod.com/ats/careersite/search.aspx?site=48&c=kypersonnelcabinet"
    csv_filename = "ky_job_links.csv"
    job_links = []

    print(f"Scraping: {BASE_URL}")
    driver.get(BASE_URL)

    try:
        # Wait until job links are visible on the first page
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href^="JobDetails.aspx"]'))
        )

        while True:
            print(f"Scraping page...")

            # Wait for job links to load properly before extracting
            WebDriverWait(driver, 10).until(
                EC.visibility_of_all_elements_located((By.CSS_SELECTOR, 'a[href^="JobDetails.aspx"]'))
            )

            # Extract job links
            job_elements = driver.find_elements(By.CSS_SELECTOR, 'a[href^="JobDetails.aspx"]')

            if job_elements:
                for job in job_elements:
                    link = job.get_attribute("href")
                    if link and [link] not in job_links:  # Avoid duplicate links
                        job_links.append([link])
                        print(f"Found job: {link}")
            else:
                print(f"No job links found on this page.")

            # Try to find the "Next" button using the aria-label attribute
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, 'a[aria-label="Next Page"]')
                ActionChains(driver).move_to_element(next_button).perform()

                # Wait for the next page to load properly before clicking
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(next_button)
                )
                next_button.click()
                time.sleep(5)  # Wait a bit longer to make sure the next page has fully loaded
                print("Clicked 'Next' button.")

            except Exception as e:
                print(f"No more pages or error: {e}")
                break  # Stop when there are no more pages or the next button can't be clicked

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
