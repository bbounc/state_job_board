import csv
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

# This scrapper works for when the url doesnt update for each new page so instead it goes through each plage gathering data and clicking next page

# Function to create a new WebDriver session
def create_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode (no GUI)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Start WebDriver session
def start_scraping():
    driver = create_driver()

    # URL of the job listings page
    BASE_URL = "https://work4.illinois.gov/jobtitle.html"
    csv_filename = "il_job_links.csv"
    job_links = []

    print(f"Scraping: {BASE_URL}")
    driver.get(BASE_URL)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href^="/jobtitle/jobtitledetails.html"][target="_blank"]'))
        )

        # Extract initial job links
        job_elements = driver.find_elements(By.CSS_SELECTOR, 'a[href^="/jobtitle/jobtitledetails.html"][target="_blank"]')
        for job in job_elements:
            link = job.get_attribute("href")
            if link:
                job_links.append([link])
                print(f"Found job: {link}")

        # Simulate clicking the "Next" button to navigate to the next page
        while True:
            try:
                # Wait for the "Next" button to be available
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'a.next'))
                )
                next_button = driver.find_element(By.CSS_SELECTOR, 'a.next')

                # Scroll to the next button to make sure it's visible
                ActionChains(driver).move_to_element(next_button).perform()
                next_button.click()
                print("Clicked 'Next' button.")

                # Wait for the page to load before extracting new job links
                time.sleep(3)  # Adjust this if needed

                # Ensure new job links are loaded after page change
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href^="/jobtitle/jobtitledetails.html"][target="_blank"]'))
                )

                # Extract new job links
                job_elements = driver.find_elements(By.CSS_SELECTOR, 'a[href^="/jobtitle/jobtitledetails.html"][target="_blank"]')
                for job in job_elements:
                    link = job.get_attribute("href")
                    if link and [link] not in job_links:  # Avoid duplicate links
                        job_links.append([link])
                        print(f"Found job: {link}")

            except Exception as e:
                print(f"Error: Could not find 'Next' button or no more jobs - {e}")
                break  # Exit the loop if there's no "Next" button or if all jobs are loaded

    except Exception as e:
        print(f"Error during initial scraping setup: {e}")
    finally:
        # Save job links to CSV after the loop finishes
        if job_links:
            with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["Job Link"])
                writer.writerows(job_links)
            print(f"Total jobs scraped: {len(job_links)}")
            print(f"Job links saved to {csv_filename}")
        else:
            print("No job links found to save.")
        
        # Close Selenium session
        driver.quit()

# Restart the process if session is lost
try:
    start_scraping()
except Exception as e:
    print(f"Error occurred: {e}")
    print("Restarting scraping session...")
    start_scraping()
