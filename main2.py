import scrapy
from scrapy.crawler import CrawlerProcess
import pandas as pd
import os
import sqlite3
from fuzzywuzzy import fuzz
import re
import subprocess
from extract_job_fields import extract_fields_with_nlp
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import locale

SCRAPER_DIR = os.path.join(os.path.dirname(__file__), 'scrapers')
# Place this at the top level (outside the class)
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

# Function to run all scraper files in the scrapers folder
def run_scrapers():
    scraper_files = [f for f in os.listdir(SCRAPER_DIR) if f.endswith('.py')]
    for file in scraper_files:
        file_path = os.path.join(SCRAPER_DIR, file)
        print(f"Running scraper: {file}")
        subprocess.run(['python', file_path], check=True)

# Constants
FUZZY_THRESHOLD = 75
TITLE_KEYWORDS = ["title", "Title", "rtltextaligneligible", "JobBulletinTitle", "Working Title","data-careersite-propertyid"]

FIELD_LABELS = {
            "deadline": [
                "Closing Date", "Deadline", "Application Due", "Apply By", "Submission Deadline", "FILING DEADLINE",
                "Last Date to Apply", "Final Application Date", "End Date", "Closing Deadline", "Submission Cutoff",
                "Job Closes", "Job Posting Closes", "Cutoff Date", "Expiration Date", "Final Filing Date",
                "Due Date", "Application Cutoff", "Apply Until", "Last Day to Submit", "Final Date", "Last Filing Date",
                "Recruitment Closes", "Recruitment Deadline", "Last Date", "Final Submission Date", "Last Day to Apply",
                "Application Close Date", "Application Period Ends", "End of Application Period", "Final Apply By Date",
                "Application Deadline", "Closing Application Date", "Hiring Deadline", "Offer Deadline", "Candidate Deadline",
                "Resume Submission Deadline", "Application Period Close Date", "Posting Closes", "Closing Time",
                "Final Opportunity to Apply", "Acceptance Deadline"
            ],
            "salary": [
                "Salary", "Pay", "Compensation", "Annual Salary", "Hiring Range - Min.",
                "Base Pay", "Salary Range", "Pay Scale", "Salary Band", "Compensation Package",
                "Hourly Wage", "Annual Compensation", "Monthly Salary", "Weekly Pay", "Biweekly Pay",
                "Starting Salary", "Pay Grade", "Wage", "Earnings", "Gross Salary", "Net Salary",
                "Remuneration", "Stipend", "Pay Rate", "Rate of Pay", "Salary Expectation", "Base Salary",
                "Salary Expectations", "Minimum Salary", "Maximum Salary", "Hourly Rate", "Yearly Salary",
                "Gross Pay", "Take-home Pay", "Income", "Financial Compensation", "Payscale",
                "Wage Rate", "Job Pay", "Employment Compensation", "Job Earnings", "Salary Estimate",
                "Total Compensation", "Salary Package", "Pay Range", "Offered Salary", "Declared Salary",
                "Anticipated Salary", "Projected Salary", "Agreed Salary", "Stated Salary"
            ]
        }

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
    "urban development analyst", "budget and policy analyst", "financial analyst", "property analyst",

    # Related Tech & Engineering
    "software development consultant", "systems optimization engineer", "cloud solutions engineer",
    "cybersecurity policy analyst", "computational linguist", "gis data analyst",
    "blockchain data engineer", "healthcare data scientist", "smart cities researcher",
    "transportation engineer", "field engineer", "project manager", "space planning analyst",
    "construction engineering", "information technology technician", "it program manager",
    "electronic technical specialist", "clinical coordinator", "emergency medical technician",
    "laboratory scientist", "aquatic biologist", "assistant medical examiner",
    "board certified behavior analyst", "behavioral health clinician", "brfss epidemiologist",
    "iys epidemiologist", "clinical dietitian", "adjunct biology instructor", "adjunct chemistry instructor",
    "adjunct clinical nursing instructor", "adjunct computer networking instructor",
    "adjunct computer programming instructor", "adjunct computer technology instructor",
    "adjunct dental assisting instructor", "adjunct electronics engineering technology instructor",
    "environmental project manager", "environmental biologist", "veterinary technology instructor",
    "autopsy technician", "certified nursing assistant", "certified medication aide",
    "health care technician", "physical science researcher", "scientist", "grants specialist",
    "state administrative manager", "departmental analyst", "ui program associate",

    # Engineering roles
    "engineer", "engineering", "engineer I", "engineer II", "engineer III", "engineer IV", "engineer V", 
    "program manager engineer", "engineering technician", "engineer program manager", "stormwater engineer",
    "engineering specialist", "civil engineer", "mechanical engineer", "electrical engineer", "environmental engineer",
    "software engineer", "systems engineer", "project engineer", "structural engineer", "chemical engineer",
    "aerospace engineer", "biomedical engineer", "geotechnical engineer", "safety engineer", "process engineer",
    "energy engineer", "systems engineering technician", "construction engineer", "transportation engineer",
    "materials engineer", "industrial engineer", "network engineer", "telecommunications engineer", "INFORMATION TECHNOLOGY",

    # Nursing & Healthcare (new additions)
    "registered nurse", "nurse", "nursing assistant", "nurse practitioner",
    "aprn", "licensed practical nurse", "lpn", "healthcare worker", "clinical nurse",
    "public health nurse", "healthcare analyst", "medical researcher", "aprn nurse",
    "advanced practice registered nurse", "mental health nurse",

    # IT & Databases (new additions)
    "information technology", "it specialist", "it technician", "it analyst",
    "it manager", "it support", "it administrator", "cybersecurity specialist",
    "network administrator", "network technician", "database administrator",
    "database analyst", "data administrator", "systems administrator",

    # Legal & Law-related (new additions)
    "lawyer", "attorney", "legal analyst", "compliance officer",
    "legal consultant", "paralegal", "general counsel", "corporate lawyer",
    "litigation specialist", "regulatory affairs analyst", "legal researcher",

    # Accounting & Finance (new additions)
    "accountant", "cpa", "certified public accountant", "tax accountant",
    "financial auditor", "auditor", "cost accountant", "staff accountant",
    "budget accountant", "controller", "financial controller",
    "accounts payable specialist", "accounts receivable specialist"
]




EXCLUDED_TITLES = [
    "CalCareers", "FOR ALL JOB SEEKERS", "STATE OF COLORADO JOB OPPORTUNITIES", "JOB OPPORTUNITIES", 
    "State of Tennessee Job Information", "Member Services", "Review Vacancy", "stateoftn-careers.ttcportals.com", 
    "Similar Jobs", "Workplace Alaska", "State Job Opportunities", "Our state. Your future. Discover the possibilities.",
    "Job Description and Duties", "Login", "Open Rank", "statecareers.idaho.gov", "Job Search Results",
    "STATE OF UTAH JOB OPPORTUNITIES", "STATE OF MICHIGAN JOB OPENINGS", "CIVIL SERVICE JOBS", "Job Title", "Civil Service Jobs",
    "State of Michigan Job Openings","State of Hawai'i, Executive Branch", "Job Seekers",".",
    "CURRENT OPENINGS", "Job Opportunities", "State of Colorado Job Opportunities", "for All Job Seekers", "Job Opportunities", 
    "Working Conditions", "State of Utah Job Opportunities", "WorkLife Elevated","Title Details", "Position Information",
"Delaware Employment Link", "here", "Summary","Minimum Requirements", "Work for Indiana", "Apply Now","A Day in the Life:", "Additional Documents", "Minimum Qualifications", "Functions",
"What You'll Need for Success:", "Job Details", "Dimensions", "Knowledge, Skills and Abilities"
]

SALARY_LABELS = ["Salary", "Pay", "Compensation", "Annual Salary", "Hiring Range - Min."]
DEADLINE_LABELS = ["Closing Date", "Deadline", "Application Due", "Apply By", "Submission Deadline", "FILING DEADLINE"]

BLUE_SYMBOL = "\033[94m🔵\033[0m"


class JobScraperSpider(scrapy.Spider):
    name = 'job_scraper'
    
    def __init__(self, max_links=10000, *args, **kwargs):
        super(JobScraperSpider, self).__init__(*args, **kwargs)
        self.max_links = max_links
        self.processed_files = []

        # Load environment variables (assuming you have a .env file with your DB credentials)
        load_dotenv()

        # Connect to PostgreSQL database (Render database connection)
        try:
            self.conn = psycopg2.connect("postgresql://db_agdu_user:jPtjXy0aH79w0Ai2ICNOD7XSrzhCY2OL@dpg-cvp9ilc9c44c73c01fpg-a.virginia-postgres.render.com/db_agdu")
            self.cursor = self.conn.cursor()

            # Create the jobs table if it doesn't exist
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS jobs (
                    id SERIAL PRIMARY KEY,
                    state TEXT,
                    title TEXT,
                    pay TEXT,
                    deadline TEXT,
                    link TEXT UNIQUE
                )
            ''')
            self.conn.commit()
            print("right main2.py")
            self.logger.info(f"{BLUE_SYMBOL} {BLUE_SYMBOL}  YYYYY Connected to the database and created jobs table.")
        except Exception as e:
            self.logger.error(f"Error connecting to the database: {str(e)}")
            raise

    def clear_database(self):
        """Clears the jobs table before inserting new data"""
        self.cursor.execute('DELETE FROM jobs')  # Deletes all data from the table
        self.conn.commit()
        self.logger.info("✅ Cleared existing data from the database.")

    def start_requests(self):
        self.clear_database()
        csv_files = [file for file in os.listdir() if file.endswith(".csv")]
        print(f"CSV files found: {csv_files}")
        for file in csv_files:
            self.processed_files.append(file)
            state_abbr = file[:2].upper()
            df = pd.read_csv(file)
            if "Job Link" not in df.columns:
                self.logger.warning(f"⚠ No 'Job Link' column in {file}")
                continue

            links = df["Job Link"].dropna().unique()
            for i, link in enumerate(links):
                if i >= self.max_links:
                    self.logger.info(f"✅ Reached max links limit ({self.max_links}) for {file}")
                    break

                self.logger.info(f"📥 Scraping link: {link}")
                yield scrapy.Request(
                    url=link,
                    callback=self.parse_job_details,
                    errback=self.handle_error,
                    meta={'state': state_abbr, 'job_link': link}
                )

    def handle_error(self, failure):
        self.logger.error(f"🚫 Failed to fetch URL: {failure.request.meta['job_link']} - {failure.value}")


# Set the locale to the US for proper currency formatti

    def categorize_salary(self, salary_str, is_stem):
            # If salary is None or empty, return 'N/A'
            if not salary_str or (isinstance(salary_str, str) and salary_str.strip().lower() in ["na", "n/a", "none", ""]):
                return 'N/A', True  # STEM jobs without salary can still be inserted

            if not isinstance(salary_str, str):
                salary_str = str(salary_str)  # Ensure it's a string

            def clean_number(salary_str):
                try:
                    cleaned = ''.join(c for c in salary_str if c.isdigit() or c == '.')
                    return float(cleaned) if cleaned else None
                except ValueError:
                    return None

            clean_salary = clean_number(salary_str)

            if clean_salary is None:
                return 'N/A', False  # Invalid salary, don't add to DB

            # Categorize salary and convert to yearly salary
            if clean_salary < 500:
                yearly_salary = clean_salary * 40 * 52
            elif clean_salary < 10_000:
                yearly_salary = clean_salary * 12
            else:
                yearly_salary = clean_salary

            # Main salary threshold (50k)
            if yearly_salary >= 80_000:
                return f"${yearly_salary:.2f} per year", True

            # If not above the main threshold, check if it's a STEM job and falls under the secondary threshold
            if is_stem:
                # Secondary salary threshold for STEM jobs (e.g., $30,000)
                if yearly_salary >= 55_000:
                    return f"${yearly_salary:.2f} per year", True

            return 'N/A', False  # Exclude jobs below the threshold

    def parse_job_details(self, response):
            if response.status in [403, 404]:
                self.logger.warning(f"⚠ Skipping {response.url} - HTTP {response.status}")
                return

            title = self.extract_job_title(response)
            if not title:
                self.logger.warning(f"⚠ No valid job title found for {response.url}")
                return

            description = " ".join(response.css("p::text").getall()).strip()
            if not description:
                self.logger.warning(f"⚠ No job description found for {title} - Skipping")
                return

            # Check if the job title matches a STEM-related keyword (fuzzy matching)
            fuzzy_score = max(fuzz.partial_ratio(description.lower(), keyword) for keyword in STEM_KEYWORDS)

            if fuzzy_score >= FUZZY_THRESHOLD:
                self.logger.info(f"✅ STEM job found: {title}")

                plain_text = " ".join(response.xpath("//body//text()").getall())
                extracted_fields = extract_fields_with_nlp(plain_text)
                deadline = extracted_fields.get("deadline", "NA")
                salary = extracted_fields.get("salary", "NA")

                # Now call categorize_salary to get the adjusted salary and whether it should be inserted
                adjusted_salary, should_insert = self.categorize_salary(salary, True)

                if should_insert:
                    self.cursor.execute('''
                        INSERT INTO jobs (state, title, pay, deadline, link)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (link) DO NOTHING;
                    ''', (
                        response.meta['state'],
                        title,
                        adjusted_salary,
                        deadline,
                        response.url
                    ))
                    self.conn.commit()
                    self.logger.info(f"✅ Job inserted into DB: {title}")
                else:
                    self.logger.info(f"❌ Job excluded based on salary: {title}")
            else:
                self.logger.info(f"❌ Not a STEM job: {title}")

        

    def extract_job_title(self, response):
        headers = response.xpath("//h1 | //h2 | //h3").getall()
        for h in headers:
            match = re.search(r'title="([^"]+)"', h)
            title = match.group(1).strip() if match else scrapy.Selector(text=h).xpath("//text()").get(default="").strip()
            if title and title not in EXCLUDED_TITLES:
                self.logger.debug(f"Found job title: {title}")
                return " ".join(title.split()[:5])
        return None

    def closed(self, reason):
        self.logger.info(f"{BLUE_SYMBOL} The following CSV files were processed: {', '.join(self.processed_files)}")
        self.conn.commit()
        self.conn.close()



if __name__ == '__main__':
    #run_scrapers()
    max_links = 100000

    process = CrawlerProcess({
        'CONCURRENT_REQUESTS': 32,
        'DOWNLOAD_DELAY': 0.3,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
        'LOG_LEVEL': 'INFO',
        'RETRY_TIMES': 3,
        'DOWNLOAD_TIMEOUT': 15,
        'COOKIES_ENABLED': False,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 5,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 5,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 403],
    })

    process.crawl(JobScraperSpider, max_links=max_links)
    process.start()
