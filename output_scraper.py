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

STEM_KEYWORDS = [
    "data science", "machine learning", "python", "statistics", "computer science",
    "software", "developer", "engineer", "engineering", "mathematics", "AI",
    "artificial intelligence", "cybersecurity", "cloud", "robotics", "biology",
    "chemistry", "physics", "quantum", "astronomy", "geology", "environmental science",
    "biomedical", "biotech", "electrical", "mechanical", "civil engineering", "coding"
]

THREAD_LIMIT = 8  # Check your corse count before running

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
    service = Service("/opt/homebrew/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(3) 
    return driver

def scrape_job_details(link, results, driver, job_index, total_jobs):
    print(f"🌍 [{job_index}/{total_jobs}] Opening: {link}")
    try:
        driver.get(link)
        wait = WebDriverWait(driver, 7)  
        wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "h1")))
        
        # Extract all header elements (h1 to h6) and get the first non-blank one, ignoring headers and their children
        headers = driver.find_elements(By.XPATH, "//h1[not(ancestor::header)] | //h2[not(ancestor::header)] | //h3[not(ancestor::header)] | //h4[not(ancestor::header)] | //h5[not(ancestor::header)] | //h6[not(ancestor::header)]")
        title = next((header.text.strip() for header in headers if header.text.strip()), "Title Not Found")
        
        description = " ".join([p.text for p in driver.find_elements(By.TAG_NAME, "p")])
        results.append((title, description, link))
        print(f"✅ [{job_index}/{total_jobs}] Successfully scraped: {title[:50]}")
    except Exception as e:
        print(f"❌ [{job_index}/{total_jobs}] Failed to fetch {link}: {e}")
        results.append(("Failed to fetch", "Failed to fetch", link))

def process_links(df):
    links = df["Job Link"].dropna().unique()
    total_jobs = len(links)

    print(f"🔍 Processing {total_jobs} jobs...")

    results = []
    job_queue = queue.Queue()

    for i, link in enumerate(links):
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
    print("🌐 Scraping job listings...")
    scraped_jobs_df = process_links(combined_df)
    scraped_jobs_df.to_csv("all_jobs.csv", index=False)
    print("🔬 Filtering for STEM-related jobs...")
    filter_jobs_by_keywords(scraped_jobs_df, STEM_KEYWORDS)
    print("✅ Process complete! Check 'all_jobs.csv' and 'filtered_jobs.csv'.")

if __name__ == "__main__":
    main()
