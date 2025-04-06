import os
import pandas as pd

from itertools import cycle
import time
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fuzzywuzzy import fuzz
import random
FUZZY_THRESHOLD = 50
START_INDEX = None  # Adjust as needed
END_INDEX = 10  # Adjust as needed
TESTING_MODE = False  # Enable/disable testing mode

TITLE_KEYWORDS = ["title", "Title", "rtltextaligneligible", "JobBulletinTitle"]

STEM_KEYWORDS = [
    # Data Science & Analytics
    "data scientist", "data science consultant", "ai engineer", "machine learning scientist",
    "data mining specialist", "predictive analytics expert", "business intelligence developer",
    "analytics translator", "statistical modeler", "cloud data engineer", "big data consultant",
    "algorithm engineer", "data warehouse engineer", "computational social scientist",
    "marketing data analyst", "operations research analyst", "bioinformatics scientist",
    "financial quantitative analyst", "computer science researcher",

    # UX/UI & Design
    "ux researcher", "ui researcher", "human-centered designer", "ux interaction designer",
    "digital product designer", "usability specialist", "accessibility ux expert",
    "mobile ux designer", "ux behavioral scientist", "cognitive ux researcher",
    "voice interface designer", "information architect", "ux strategy consultant",
    "visual experience designer", "conversational ai designer", "service designer",
    "inclusive design specialist", "ar/vr ux developer",

    # Program Evaluation & Research
    "research & evaluation specialist", "policy impact analyst", "program performance auditor",
    "social impact researcher", "mixed methods researcher", "public policy researcher",
    "applied econometrics expert", "community program evaluator", "nonprofit program analyst",
    "strategic impact consultant", "government performance analyst", "implementation scientist",
    "evidence-based policy expert", "social data analyst", "software development", "computer science",

    # Policy & Budget Analysis
    "policy analyst", "budget analyst", "public policy advisor", "economic policy analyst",
    "fiscal impact analyst", "government finance consultant", "public administration analyst",
    "revenue forecasting specialist", "workforce policy researcher", "cost-benefit evaluation expert",
    "legislative budget analyst", "regulatory impact consultant", "expenditure policy strategist",
    "tax policy analyst", "macroeconomic researcher", "public finance economist",
    "urban development analyst",

    # Related Tech & Engineering
    "software development consultant", "systems optimization engineer", "cloud solutions engineer",
    "cybersecurity policy analyst", "computational linguist", "gis data analyst",
    "blockchain data engineer", "healthcare data scientist", "smart cities researcher"
]

EXCLUDED_TITLES = [
    "CalCareers", "FOR ALL JOB SEEKERS", "STATE OF COLORADO JOB OPPORTUNITIES", "JOB OPPORTUNITIES", 
    "State of Tennessee Job Information", "Member Services", "Review Vacancy", "stateoftn-careers.ttcportals.com", 
    "Similar Jobs", "Workplace Alaska", "State Job Opportunities", "Our state. Your future. Discover the possibilities.", 
    "Job Description and Duties", "Login", "Open Rank", "statecareers.idaho.gov", "Job Search Results", 
    "STATE OF UTAH JOB OPPORTUNITIES", "STATE OF MICHIGAN JOB OPENINGS", "CIVIL SERVICE JOBS", "Job Title", 
    "Application Template", "Freename Application", "State of Hawai'i, Executive Branch", "worklife elevated", ".", "worklife elevated",
    "Careers with the State of NC", "apply now", "Apply Now", "Apply now", "Minimum Requirements", "Job Description", "Position Information", "SEARCH JOBS SAVED JOBS BENEFIT", "Description of Job", "Job Responsibilities", "Position Details", "Title Details", "CURRENT OPENINGS", ""
]

def get_driver():
    """Creates and returns a Selenium WebDriver instance."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    service = Service("/opt/homebrew/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(2)
    return driver

def extract_job_title(driver, title_keywords, excluded_titles):
    """Extracts the job title with keyword priority from headers and class attributes."""
    headers = driver.find_elements(By.XPATH, "//h1 | //h2 | //h3")
    class_elements = driver.find_elements(By.XPATH, "//*[@class]")
    
    potential_title = None
    
    # Check header elements first
    for h in headers:
        text = h.text.strip()
        if text and text not in excluded_titles:
            if any(keyword.lower() in text.lower() for keyword in title_keywords):
                return " ".join(text.split()[:5])  # Return first 5 words
            potential_title = text  # Store as fallback
    
    # Check class-based elements if no title was found in headers
    for element in class_elements:
        class_attr = element.get_attribute("class")
        text = element.text.strip()
        if text and text not in excluded_titles:
            if any(keyword.lower() in class_attr.lower() or keyword.lower() in text.lower() for keyword in title_keywords):
                return " ".join(text.split()[:5])  # Return first 5 words
    
    return " ".join(potential_title.split()[:5]) if potential_title else None  # Return first 5 words of fallback title

def fuzzy_match(description):
    """Fast fuzzy matching using RapidFuzz"""
    description = description.lower()
    return any(fuzz.partial_ratio(keyword, description) >= 90 for keyword in STEM_KEYWORDS)

def scrape_job_details(link, driver, state):
    """Scrapes job details and prioritizes job titles based on keyword matches."""
    for attempt in range(2):  # Max 2 retries
        try:
            driver.get(link)
            WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            title = extract_job_title(driver, TITLE_KEYWORDS, EXCLUDED_TITLES)
            if title:
                print(f"🔎 Found Job Title: {state.upper()} - {title[:30]}")  # Print state and title capped at 30 characters
            else:
                print(f"⚠ No job title found for {link}")
                time.sleep(random.uniform(0.5, 2))  # Short retry delay
                continue

            # Perform fuzzy matching on the job title or description
            description = " ".join([p.text for p in driver.find_elements(By.TAG_NAME, "p") if p.text.strip()])
            if not description:
                return None  # Skip if no description
            
            fuzzy_score = max([fuzz.partial_ratio(keyword, description.lower()) for keyword in STEM_KEYWORDS], default=0)
            if fuzzy_score >= FUZZY_THRESHOLD:
                print(f"✅ STEM job found: {title}")
                return state, title, "NA", "NA", link  # Return State, Title, and default Pay/Deadline + Link
            else:
                print(f"❌ Not a STEM job: {title}")
                return None
        except Exception as e:
            print(f"❌ ERROR: Failed to scrape {link} ({e})")
            time.sleep(random.uniform(0.5, 2))  # Reduce retry time
    
    return None  # Return None if scraping fails after retries

def process_csv(file_path, driver, skipped_files, link_limit=None):
    """Processes a CSV file, scrapes job details, and collects state-title pairs."""
    print(f"📄 Processing: {file_path}")
    state = file_path[:2].lower()  # Extract state code from file name
    df = pd.read_csv(file_path)
    links = df["Job Link"].dropna().unique()

    if link_limit:
        links = links[:link_limit]  # Limit the number of links to scrape

    results = []

    for i, link in enumerate(links):
        result = scrape_job_details(link, driver, state)
        if result:
            state, title, pay, deadline, link = result  # Capture link from the result
            results.append((state.upper(), title, pay, deadline, link))  # Include the link in the results

        # Progress tracking
        progress = (i + 1) / len(links) * 100
        if i % 10 == 0:
            print(f"{file_path}: {progress:.2f}% complete")
        
        if link_limit and i >= link_limit - 1:  # Stop after processing the limit
            break

    # Write results to CSV
    if results:
        results_df = pd.DataFrame(results, columns=["State", "Job Title", "Pay", "Deadline", "Job Link"])  # Add "Job Link"
        results_df.to_csv("filtered_jobs.csv", mode="a", index=False, header=not os.path.exists("filtered_jobs.csv"))
        print(f"✅ Processed {len(results)} STEM jobs from {file_path}")
    else:
        print(f"⚠ No STEM jobs found in {file_path}")

def main():
    """Main function to initialize scraping across multiple threads."""
    print("🚀 Starting job scraping...")
    csv_files = [file for file in os.listdir() if file.endswith(".csv")]
    print(f"🔍 Found {len(csv_files)} CSV files.")

    # Use 6 browser instances for concurrency
    drivers = [get_driver() for _ in range(6)]
    driver_cycle = cycle(drivers)
    skipped_files = []

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(process_csv, file, next(driver_cycle), skipped_files, link_limit=END_INDEX): file for file in csv_files}

        for future in futures:
            try:
                future.result()  # Ensure errors inside `process_csv()` are raised
            except Exception as e:
                print(f"❌ Error processing {futures[future]}: {e}")

    # Close all WebDriver instances
    for driver in drivers:
        driver.quit()

    print(f"✅ Scraping completed.\n🚫 Skipped {len(skipped_files)} files: {skipped_files}")

if __name__ == "__main__":
    main()
