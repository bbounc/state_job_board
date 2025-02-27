import os
import pandas as pd
from fuzzywuzzy import fuzz

import re
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# List of STEM-related keywords to filter jobs
STEM_KEYWORDS = [
    # Data Science Keywords
    "data scientist", "machine learning engineer", "ai researcher", "deep learning engineer",
    "nlp engineer", "predictive modeler", "data engineer", "big data architect",
    "statistical analyst", "quantitative modeler", "r programmer", "sql specialist",
    "cloud data engineer", "etl developer", "a/b test analyst", "neural network specialist",
    "forecasting analyst", "distributed systems engineer", "data pipeline architect",
    "time series forecaster", "data ethics consultant",

    # UX Designer Keywords
    "ux researcher", "ux strategist", "interaction designer", "ui designer",
    "user researcher", "usability analyst", "wireframe specialist",
    "design system architect", "visual ux designer", "accessibility designer",
    "figma expert", "adobe xd specialist", "sketch designer",
    "motion ux designer", "responsive ux expert", "user journey mapper",
    "human factors specialist", "heuristic evaluator", "mobile ux designer",
    "ux prototyper",

    # Program Evaluator Keywords
    "program evaluation specialist", "impact evaluation analyst",
    "performance metrics analyst", "qualitative research consultant",
    "quantitative evaluator", "policy evaluation expert",
    "cost-benefit analyst", "kpi strategist", "stakeholder assessment specialist",
    "public sector evaluator", "mixed methods researcher",
    "government program evaluator", "randomized trial analyst",
    "evidence-based policy consultant",

    # Policy & Budget Analyst Keywords
    "policy analyst", "budget analyst", "fiscal policy expert", 
    "public finance consultant", "government budget strategist",
    "economic policy researcher", "cost analyst", "legislative fiscal analyst",
    "revenue forecaster", "performance budgeting specialist",
    "tax policy expert", "workforce policy analyst", "expenditure reviewer",
    "public expenditure strategist", "capital budget planner"
]

EXCLUDED_TITLES = [
    "CalCareers", "FOR ALL JOB SEEKERS", "STATE OF COLORADO JOB OPPORTUNITIES", "JOB OPPORTUNITIES", 
    "State of Tennessee Job Information", "Member Services", "Review Vacancy", "stateoftn-careers.ttcportals.com", 
    "Similar Jobs", "Workplace Alaska", "State Job Opportunities", "Our state. Your future. Discover the possibilities.", 
    "Job Description and Duties", "Login", "Open Rank", "statecareers.idaho.gov", "Job Search Results", 
    "STATE OF UTAH JOB OPPORTUNITIES", "STATE OF MICHIGAN JOB OPENINGS", "CIVIL SERVICE JOBS", "Job Title", 
    "Application Template", "Freename Application", "State of Hawai'i, Executive Branch", "worklife elevated", ".", "worklife elevated",
    "Careers with the State of NC", "apply now"
]


# Fuzzy matching threshold (adjust as needed)
FUZZY_THRESHOLD = 85

def fuzzy_match(description, keywords, threshold=FUZZY_THRESHOLD):
    """Returns True if any keyword is fuzzily matched in the description."""
    description = description.lower()
    for keyword in keywords:
        if fuzz.partial_ratio(keyword.lower(), description) >= threshold:
            return True
    return False

def filter_jobs_by_keywords(df, keywords):
    """
    Filters job listings using fuzzy matching on job descriptions.
    """
    print("Filtering jobs using fuzzy keyword matching...")
    df["Job Title"] = df["Job Title"].fillna("").str.lower()
    df["Job Description"] = df["Job Description"].fillna("").str.lower()

    # Apply fuzzy matching
    filtered_df = df[df["Job Description"].apply(lambda desc: fuzzy_match(desc, keywords))]
    
    print(f"✅ Filtered down to {len(filtered_df)} jobs using fuzzy matching.")
    return filtered_df



  
def get_driver(headless=True):
    """
    Sets up the Selenium WebDriver with the required options.

    Parameters:
        headless (bool): Whether to run the driver in headless mode (default: True).

    Returns:
        WebDriver: A Selenium WebDriver instance configured for scraping.
    """
    print("Setting up Selenium driver...")
    options = Options()
    if headless:
        options.add_argument("--headless")  # Run the WebDriver in headless mode
    service = Service("/opt/homebrew/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")  # Bypass detection
    driver.implicitly_wait(3)
    print("Selenium driver setup complete.")
    return driver

def scrape_job_details(link, driver, state, job_index, total_jobs, max_retries=3):
    """
    Scrapes the details of a single job listing.

    Parameters:
        link (str): The URL of the job listing.
        driver (WebDriver): The Selenium WebDriver instance.
        state (str): The state associated with the job.
        job_index (int): The index of the job being scraped (for progress tracking).
        total_jobs (int): The total number of jobs to scrape (for progress tracking).
        max_retries (int): The maximum number of retry attempts in case of failure (default: 3).

    Returns:
        tuple: A tuple containing the job title, job description, job link, and state, or None if the scraping failed.
    """
    print(f"Scraping job {job_index}/{total_jobs}: {link}")
    retries = 0
    while retries < max_retries:
        try:
            driver.delete_all_cookies()
            driver.get(link)

            wait = WebDriverWait(driver, 15)  # Increased wait time for slower pages
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            if "Access Forbidden" in driver.page_source or "403" in driver.title:
                print(f"Access Forbidden or 403 Error for {link}")
                return None  # Skip storing this result

            # Extract headers and try to get a valid title
            headers = driver.find_elements(By.XPATH, "//h1 | //h2 | //h3 | //div[contains(@class, 'title')] | //span[contains(@class, 'title')]")
            header_texts = [h.text.strip() for h in headers if h.text.strip()]

            title = None
            for text in header_texts:
                # Normalize case and remove extra spaces for comparison
                if text.lower().strip() not in [excluded.lower() for excluded in EXCLUDED_TITLES]:
                    title = text
                    break  # Stop at the first valid title found

            if not title:
                print(f"No valid title found for {link}. Retrying...")
                retries += 1
                time.sleep(random.uniform(2, 5))  # Randomized sleep to avoid detection
                continue  # Retry fetching the page

            # Extract job description
            paragraphs = driver.find_elements(By.TAG_NAME, "p")
            description = " ".join([p.text for p in paragraphs if p.text.strip()])

            # Return job details
            print(f"Successfully scraped job: {title}")
            return (title, description, link, state)
        except Exception as e:
            print(f"Error scraping {link}: {e}. Retrying...")
            retries += 1
            time.sleep(random.uniform(2, 5))  # Randomized wait before retrying
    return None

def process_and_filter_file(file_path, driver, keywords, output_file="filtered_jobs.csv", start_index=None, stop_index=None):
    """
    Processes each CSV file, scrapes job listings, filters them, and writes the results to a CSV file.

    Parameters:
        file_path (str): The path to the CSV file containing job links.
        driver (WebDriver): The Selenium WebDriver instance.
        keywords (list): The list of keywords to filter the job listings by.
        output_file (str): The output file where the filtered jobs will be saved (default: "filtered_jobs.csv").
        start_index (int): The index to start processing links from (default: None).
        stop_index (int): The index to stop processing links at (default: None).

    Returns:
        None
    """
    print(f"Processing file: {file_path}")
    state = file_path[:2].lower()  # Extract state from the file name (first two letters)

    # Read the file into a DataFrame
    df = pd.read_csv(file_path)
    links = df["Job Link"].dropna().unique()

    # Apply start/stop indices to limit the links to process
    if start_index is not None:
        links = links[start_index:]
    if stop_index is not None:
        links = links[:stop_index]

    total_jobs = len(links)

    results = []

    # Loop through all job links in the current file
    for i, link in enumerate(links, start=1):
        job_details = scrape_job_details(link, driver, state, i, total_jobs)
        if job_details:
            results.append(job_details)

    # Create DataFrame from the results
    results_df = pd.DataFrame(results, columns=["Job Title", "Job Description", "Job Link", "State"])

    # Filter jobs by STEM keywords
    filtered_df = filter_jobs_by_keywords(results_df, keywords)

    # Write to the output file (append mode)
    filtered_df.to_csv(output_file, mode="a", header=not os.path.exists(output_file), index=False)

    # Print job count to the console
    job_count = len(filtered_df)
    print(f"✅ {job_count} jobs added to {output_file}")

    print(f"Finished processing file: {file_path}")

def main(start_index=None, stop_index=None):
    """
    The main function to start the scraping process, process all CSV files, and filter jobs.

    Parameters:
        start_index (int): The index to start processing links from (default: None).
        stop_index (int): The index to stop processing links at (default: None).

    Returns:
        None
    """
    print("Starting scraping process...")
    driver = get_driver()  # Set up the Selenium WebDriver
    try:
        # List all CSV files in the current directory
        csv_files = [file for file in os.listdir() if file.endswith(".csv")]
        print(f"Found {len(csv_files)} CSV files to process.")

        for file in csv_files:
            print(f"Processing file: {file}")
            process_and_filter_file(file, driver, STEM_KEYWORDS, start_index=start_index, stop_index=stop_index)

    finally:
        driver.quit()  # Ensure that the driver is quit after processing all files
        print("Scraping process completed.")

if __name__ == "__main__":
    # Example: Set start_index=0 and stop_index=10 to process the first 10 links from each file
    main(start_index=0, stop_index=30)
