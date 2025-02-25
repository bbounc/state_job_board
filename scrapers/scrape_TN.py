import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from fake_useragent import UserAgent
from selenium_stealth import stealth
import time
import random
import csv
import ssl
import certifi

# Fix SSL certificate issues
ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())

# Function to create a stealthy WebDriver session
def create_driver():
    options = uc.ChromeOptions()

    # Use a fake user-agent to mimic a real browser
    ua = UserAgent()
    options.add_argument(f"user-agent={ua.random}")

    # Prevent bot detection
    options.add_argument("--disable-blink-features=AutomationControlled")

    # Create the driver
    driver = uc.Chrome(options=options, use_subprocess=True)

    # Apply stealth mode to avoid detection
    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )

    return driver

# Function to handle CAPTCHA manually with unlimited wait time
def wait_for_captcha(driver):
    while True:
        try:
            if driver.find_elements(By.CSS_SELECTOR, 'iframe[src*="captcha"]'):
                print("CAPTCHA detected. Please solve it in the browser...")
                input("Press Enter to continue after solving the CAPTCHA.")
            else:
                break  # Exit loop if no CAPTCHA
        except Exception as e:
            print(f"Error checking for CAPTCHA: {e}")
            break

# Start the scraping session
def start_scraping():
    driver = create_driver()
    BASE_URL = "https://stateoftn-careers.ttcportals.com/search/jobs/in?cf%5BREC_LOCATION%5D=&location=&page=1&q=#"
    csv_filename = "tn_job_links.csv"
    job_links = []

    print(f"Scraping: {BASE_URL}")
    driver.get(BASE_URL)

    # Handle CAPTCHA if present
    wait_for_captcha(driver)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a'))
        )

        while True:
            print("Extracting job links...")

            # Extract job listing links
            job_elements = driver.find_elements(By.CSS_SELECTOR, 'a[href^="https://stateoftn-careers.ttcportals.com/jobs/"]')
            for job in job_elements:
                link = job.get_attribute("href")
                if link and link not in job_links:
                    job_links.append(link)
                    print(f"Found job: {link}")

            # Locate "Next" button
            try:
                next_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'a.next_page'))
                )

                # Human-like interaction before clicking
                time.sleep(random.uniform(5, 10))  # Random delay
                ActionChains(driver).move_to_element(next_button).perform()
                time.sleep(random.uniform(2, 5))
                next_button.click()
                print("Clicked 'Next' button.")

                # Handle CAPTCHA if triggered (unlimited wait)
                wait_for_captcha(driver)

                # Wait for new page to load
                time.sleep(random.uniform(3, 6))

            except Exception as e:
                print(f"No 'Next' button found or an error occurred: {e}")
                break  # Stop if no more pages

    except Exception as e:
        print(f"Error during scraping: {e}")
    finally:
        # Save job links to CSV
        if job_links:
            with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["Job Link"])
                writer.writerows([[link] for link in job_links])
            print(f"Total jobs scraped: {len(job_links)}")
            print(f"Job links saved to {csv_filename}")
        else:
            print("No job links found to save.")

        driver.quit()

# Restart if session fails
try:
    start_scraping()
except Exception as e:
    print(f"Error occurred: {e}")
    print("Restarting scraping session...")
    start_scraping()
