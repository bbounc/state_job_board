import os
import pandas as pd
import threading
import queue
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Set the start index here instead of typing it during runtime
START_INDEX = 8000  # Change this number to start from a different index

STEM_KEYWORDS = [
    "data science", "machine learning", "python", "statistics", "computer science",
    "software", "developer", "engineer", "engineering", "mathematics", "AI",
    "artificial intelligence", "cybersecurity", "cloud", "robotics", "biology",
    "chemistry", "physics", "quantum", "astronomy", "geology", "environmental science",
    "biomedical", "biotech", "electrical", "mechanical", "civil engineering", "coding"
]

THREAD_LIMIT = 8  # Check your core count before running

def combine_csv_files(output_file="combined_jobs.csv"):
    csv_files = [file for file in os.listdir() if file.endswith(".csv")]
    if not csv_files:
        raise ValueError("No CSV files found in the directory!")

    df_list = [pd.read_csv(file) for file in csv_files]
    combined_df = pd.concat(df_list, ignore_index=True)
    link_column = next((col for col in combined_df.columns if "link" in col.lower()), None)
    if not link_column:
        raise ValueError(f"Could not find a column containing 'link' in {combined_df.columns.tolist()}")

    combined_df.rename(columns={link_column: "Job Link"}, inplace=True)
    combined_df.drop_duplicates(subset=["Job Link"], inplace=True)
    combined_df.to_csv(output_file, index=False)
    print(f"✅ Combined CSV contains {len(combined_df)} unique job links.")
    return combined_df

def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--log-level=3")
    options.add_argument("--disable-blink-features=AutomationControlled")  # Bypass bot detection
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    service = Service("/opt/homebrew/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")  # Bypass detection
    driver.implicitly_wait(3)
    return driver

def scrape_job_details(link, results, driver, job_index, total_jobs):
    print(f"🌍 [{job_index}/{total_jobs}] Opening: {link}")
    try:
        driver.delete_all_cookies()
        driver.get(link)
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        if "Access Forbidden" in driver.page_source or "403" in driver.title:
            print(f"🚫 [{job_index}/{total_jobs}] Access Forbidden: {link}")
            results.append(("Access Forbidden", "Restricted Page", link))
            return

        headers = driver.find_elements(By.XPATH, "//h1 | //h2 | //h3 | //div[contains(@class, 'title')] | //span[contains(@class, 'title')]")
        header_texts = [h.text.strip() for h in headers if h.text.strip()]
        title = header_texts[0] if header_texts else "Title Not Found"

        paragraphs = driver.find_elements(By.TAG_NAME, "p")
        description = " ".join([p.text for p in paragraphs if p.text.strip()])

        results.append((title, description, link))
        print(f"✅ [{job_index}/{total_jobs}] Scraped: {title[:50]}")
    except Exception as e:
        print(f"❌ [{job_index}/{total_jobs}] Failed to fetch {link}: {e}")
        results.append(("Failed to fetch", "Failed to fetch", link))

def process_links(df, start_index=0):
    links = df["Job Link"].dropna().unique()
    total_jobs = len(links)

    if start_index >= total_jobs:
        print("❌ Invalid start index! No jobs available at that position.")
        return pd.DataFrame(columns=["Job Title", "Job Description", "Job Link"])

    print(f"🔍 Processing {total_jobs - start_index} jobs, starting from index {start_index}...")
    results = []
    job_queue = queue.Queue()
    
    for i, link in enumerate(links[start_index:], start=start_index):
        job_queue.put((i + 1, total_jobs, link))

    def worker():
        driver = get_driver()
        while not job_queue.empty():
            job_index, total_jobs, link = job_queue.get()
            scrape_job_details(link, results, driver, job_index, total_jobs)
            job_queue.task_done()
        driver.quit()

    threads = []
    for _ in range(min(THREAD_LIMIT, job_queue.qsize())):
        thread = threading.Thread(target=worker)
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    return pd.DataFrame(results, columns=["Job Title", "Job Description", "Job Link"])

def filter_jobs_by_keywords(df, keywords, output_file="filtered_jobs.csv"):
    df["Job Description"] = df["Job Description"].fillna("")
    filtered_df = df[df["Job Description"].str.lower().apply(lambda desc: any(k in desc for k in keywords))]
    print(f"✅ Found {len(filtered_df)} STEM-related jobs.")
    filtered_df.to_csv(output_file, index=False)
    return filtered_df

def main():
    print("📂 Combining CSV files...")
    combined_df = combine_csv_files()
    start_index = min(max(START_INDEX, 0), len(combined_df) - 1)

    print("🌐 Scraping job listings...")
    scraped_jobs_df = process_links(combined_df, start_index)
    scraped_jobs_df.to_csv("all_jobs.csv", index=False)

    print("🔬 Filtering for STEM-related jobs...")
    filter_jobs_by_keywords(scraped_jobs_df, STEM_KEYWORDS)
    print("✅ Process complete! Check 'all_jobs.csv' and 'filtered_jobs.csv'.")

if __name__ == "__main__":
    main()
