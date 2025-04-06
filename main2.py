import scrapy
from scrapy.crawler import CrawlerProcess
import pandas as pd
import os
import sqlite3
from fuzzywuzzy import fuzz
import re
import subprocess
import os
from extract_job_fields import extract_fields_with_nlp


SCRAPER_DIR = os.path.join(os.path.dirname(__file__), 'scrapers')

# Function to run all scraper files in the scrapers folder
def run_scrapers():
    scraper_files = [f for f in os.listdir(SCRAPER_DIR) if f.endswith('.py')]
    for file in scraper_files:
        file_path = os.path.join(SCRAPER_DIR, file)
        print(f"Running scraper: {file}")
        subprocess.run(['python', file_path], check=True)

# Constants
FUZZY_THRESHOLD = 85
TITLE_KEYWORDS = ["title", "Title", "rtltextaligneligible", "JobBulletinTitle", "Working Title"]

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

    # Engineering roles (added)
    "engineer", "engineering", "engineer I", "engineer II", "engineer III", "engineer IV", "engineer V", 
    "program manager engineer", "engineering technician", "engineer program manager", "stormwater engineer",
    "engineering specialist", "civil engineer", "mechanical engineer", "electrical engineer", "environmental engineer",
    "software engineer", "systems engineer", "project engineer", "structural engineer", "chemical engineer",
    "aerospace engineer", "biomedical engineer", "geotechnical engineer", "safety engineer", "process engineer",
    "energy engineer", "systems engineering technician", "construction engineer", "transportation engineer",
    "materials engineer", "industrial engineer", "network engineer", "telecommunications engineer"
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
"Delaware Employment Link", "here", "Summary","Minimum Requirements", "Work for Indiana", "Apply Now","A Day in the Life:"
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

        # Connect to SQLite DB
        db_path = os.path.join(os.path.dirname(__file__), 'backend', 'jobs.db')  # Absolute path to the backend folder
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.clear_database()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                state TEXT,
                title TEXT,
                pay TEXT,
                deadline TEXT,
                link TEXT UNIQUE
            )
        ''')
        self.conn.commit()

    def clear_database(self):
            """Clears the jobs table before inserting new data"""
            self.cursor.execute('DELETE FROM jobs')  # Deletes all data from the table
            self.conn.commit()
            self.logger.info("✅ Cleared existing data from the database.")

    def start_requests(self):
        csv_files = [file for file in os.listdir() if file.endswith(".csv")]
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

                yield scrapy.Request(
                    url=link,
                    callback=self.parse_job_details,
                    errback=self.handle_error,
                    meta={'state': state_abbr, 'job_link': link}
                )

    def handle_error(self, failure):
        self.logger.error(f"🚫 Failed to fetch URL: {failure.request.meta['job_link']} - {failure.value}")

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
            # It's a STEM job, proceed with NLP extraction for salary and deadline
            self.logger.info(f"✅ STEM job found: {title}")

            plain_text = " ".join(response.xpath("//body//text()").getall())
            extracted_fields = extract_fields_with_nlp(plain_text)
            deadline = extracted_fields.get("deadline", "NA")
            salary = extracted_fields.get("salary", "NA")

            # Save to database
            self.cursor.execute('''
                INSERT OR IGNORE INTO jobs (state, title, pay, deadline, link)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                response.meta['state'],
                title,
                salary,
                deadline,
                response.url
            ))
            self.conn.commit()
        else:
            self.logger.info(f"❌ Not a STEM job: {title}")


       
    

    def extract_job_title(self, response):
        headers = response.xpath("//h1 | //h2 | //h3").getall()
        for h in headers:
            match = re.search(r'title="([^"]+)"', h)
            title = match.group(1).strip() if match else scrapy.Selector(text=h).xpath("//text()").get(default="").strip()
            if title and title not in EXCLUDED_TITLES:
                return " ".join(title.split()[:5])
        return None

    def extract_field(self, response):
        deadline_pattern = r"(?i)(?:Deadline|Apply By|Due Date|Closing Date)[:\s]*([A-Za-z]+\s\d{1,2},\s?\d{2,4}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
        salary_pattern = r"(?i)(?:Salary|Pay|Compensation|Wage)[\s:]*\s*(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*(?:to|-|–)?\s*\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"
        extracted_fields = {}

        text = response.text
        text_deadline_match = re.search(deadline_pattern, text)
        text_salary_match = re.search(salary_pattern, text)

        if text_deadline_match:
            extracted_fields['deadline'] = text_deadline_match.group(1)
        if text_salary_match:
            extracted_fields['salary'] = text_salary_match.group(1)

        tables = response.xpath('//table')
        for table in tables:
            cells = table.xpath('.//tr//td | .//tr//th')
            for cell in cells:
                cell_text = ''.join(cell.xpath('.//text()').getall()).strip()
                if 'deadline' in cell_text.lower() and 'deadline' not in extracted_fields:
                    match = re.search(deadline_pattern, cell_text)
                    if match:
                        extracted_fields['deadline'] = match.group(1)
                elif any(word in cell_text.lower() for word in ['salary', 'pay', 'wage', 'compensation']) and 'salary' not in extracted_fields:
                    match = re.search(salary_pattern, cell_text)
                    if match:
                        extracted_fields['salary'] = match.group(1)
                if 'salary' in extracted_fields and 'deadline' in extracted_fields:
                    break

        label_blocks = response.xpath("//div[contains(@class, 'term-block') or contains(@class, 'row') or contains(@class, 'info-block')]")
        for block in label_blocks:
            label = ''.join(block.xpath(".//*[contains(@class, 'label') or contains(@class, 'title') or contains(@class, 'description')]/text()").getall()).strip().lower()
            value = ''.join(block.xpath(".//*[contains(@class, 'value') or contains(@class, 'description') or contains(@class, 'text') or contains(@class, 'content') or self::p]/text()").getall()).strip()
            label = re.sub(r'\s+', ' ', label)
            value = re.sub(r'\s+', ' ', value)

            if any(term in label for term in ['deadline', 'apply by', 'due date', 'closing date']):
                if not extracted_fields.get('deadline'):
                    date_match = re.search(deadline_pattern, label + ' ' + value)
                    if date_match:
                        extracted_fields['deadline'] = date_match.group(1)
            elif any(term in label for term in ['salary', 'pay', 'compensation', 'wage']):
                if not extracted_fields.get('salary'):
                    salary_match = re.search(salary_pattern, label + ' ' + value)
                    if salary_match:
                        extracted_fields['salary'] = salary_match.group(1)

        return extracted_fields or {}

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
