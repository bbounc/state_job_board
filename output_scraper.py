import os
import pandas as pd
import aiohttp
import asyncio
from bs4 import BeautifulSoup

STEM_KEYWORDS = [
    "data science", "machine learning", "python", "statistics", "computer science",
    "software", "developer", "engineer", "engineering", "mathematics", "AI",
    "artificial intelligence", "cybersecurity", "cloud", "robotics", "biology",
    "chemistry", "physics", "quantum", "astronomy", "geology", "environmental science",
    "biomedical", "biotech", "electrical", "mechanical", "civil engineering", "coding"
]

CONCURRENT_REQUESTS = 10  # Limits active scraping requests (prevents overload)

def combine_csv_files(output_file="combined_jobs.csv"):
    """Combines all CSV files in the directory into one and identifies the link column."""
    csv_files = [file for file in os.listdir() if file.endswith(".csv")]
    df_list = [pd.read_csv(file) for file in csv_files]
    combined_df = pd.concat(df_list, ignore_index=True)

    # Identify the correct column for job links
    link_column = next((col for col in combined_df.columns if "link" in col.lower()), None)
    if not link_column:
        raise ValueError(f"Could not find a column containing 'link' in {combined_df.columns.tolist()}")

    combined_df.rename(columns={link_column: "Job Link"}, inplace=True)
    combined_df.to_csv(output_file, index=False)
    return combined_df

async def fetch_page(session, link):
    """Fetches a job page asynchronously with error handling."""
    try:
        async with session.get(link, timeout=10) as response:
            return await response.text()
    except Exception:
        return None

async def scrape_job_details(session, link):
    """Scrapes the job title and description from a given job link."""
    page_content = await fetch_page(session, link)
    if not page_content:
        return "Failed to fetch", "Failed to fetch"

    soup = BeautifulSoup(page_content, 'html.parser')

    # Extract any tag containing "title"
    title_tags = soup.find_all(lambda tag: tag.name and "title" in tag.name.lower())
    title = title_tags[0].text.strip() if title_tags else "No Title Found"

    # Extract description using <p> tags 
    description = " ".join([p.text for p in soup.find_all("p")])

    return title, description

async def process_links(df, start=2000, stop=4000):
    """Processes job links asynchronously, limiting concurrent requests."""
    job_data = []
    links = df["Job Link"].dropna().unique()[start:stop]

    connector = aiohttp.TCPConnector(limit_per_host=CONCURRENT_REQUESTS)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [scrape_job_details(session, link) for link in links]
        results = await asyncio.gather(*tasks)

    for (title, description), link in zip(results, links):
        job_data.append([title, description, link])

    return pd.DataFrame(job_data, columns=["Job Title", "Job Description", "Job Link"])

def filter_jobs_by_keywords(df, keywords, output_file="filtered_jobs.csv"):
    """Filters job listings based on STEM keywords in the description."""
    filtered_df = df[df["Job Description"].str.lower().apply(lambda desc: any(k in desc for k in keywords))]
    filtered_df.to_csv(output_file, index=False)
    return filtered_df

def main():
    print("Combining CSV files...")
    combined_df = combine_csv_files()

    print("Scraping job listings from line 2000 to 4000...")
    scraped_jobs_df = asyncio.run(process_links(combined_df, start=2000, stop=4000))
    scraped_jobs_df.to_csv("all_jobs.csv", index=False)

    print("Filtering job listings for STEM-related jobs...")
    filter_jobs_by_keywords(scraped_jobs_df, STEM_KEYWORDS)

    print("Process completed! Check 'all_jobs.csv' and 'filtered_jobs.csv'.")

if __name__ == "__main__":
    main()
