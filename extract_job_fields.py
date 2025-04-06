import spacy
from dateparser import parse
import re
from datetime import datetime

# Load SpaCy model once
nlp = spacy.load("en_core_web_sm")

def extract_salary(text):
    """Extract salary-related MONEY entities from the job posting, including the time period."""
    doc = nlp(text)
    salaries = [ent.text for ent in doc.ents if ent.label_ == "MONEY"]
    
    # Optional: Clean up and return the first plausible salary with time period (e.g., per month, annually)
    for salary in salaries:
        # Check if the salary is followed by time-related keywords like "per month", "per year", etc.
        match = re.search(r"(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(per\s*(month|year|hour|week|annum))?", salary, re.IGNORECASE)
        if match:
            return match.group(0)  # Return the matched salary string along with the time period if found
    
    return None  # Return None if no salary is found

def extract_deadline(text):
    """Extract the first date related to a deadline or closing."""
    lines = text.splitlines()
    
    # Keywords related to deadline
    deadline_keywords = [
        "deadline", "closing date", "apply by", "last day", "applications due", 
        "filing deadline", "apply before", "closing at", "closing date"
    ]
    
    # Try to extract deadline from lines containing keywords
    potential_dates = []
    
    for line in lines:
        lower_line = line.lower()
        if any(keyword in lower_line for keyword in deadline_keywords):
            date = parse(line, settings={"PREFER_DATES_FROM": "future"})
            if date:
                potential_dates.append(date)
    
    # If multiple dates are found, pick the one in the future
    if potential_dates:
        current_date = datetime.now()
        future_dates = [date for date in potential_dates if date > current_date]
        
        # Return the first future date, or the latest if there are multiple
        if future_dates:
            return min(future_dates).strftime("%Y-%m-%d")

    # Fallback: Use a more flexible regex to capture dates in various formats
    deadline_pattern = r"(?i)(?:Deadline|Apply By|Due Date|Closing Date|FILING DEADLINE|Apply before|Closing At)[:\s]*([A-Za-z]+\s\d{1,2},\s?\d{2,4}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\s?[APap][Mm]\s?[A-Za-z]+|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\s?\d{1,2}:\d{2}\s?[APap][Mm]|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
    text_deadline_match = re.search(deadline_pattern, text)
    if text_deadline_match:
        date = parse(text_deadline_match.group(1), settings={"PREFER_DATES_FROM": "future"})
        if date:
            return date.strftime("%Y-%m-%d")
    
    # Final fallback: Try extracting any date if no specific deadline found
    date = parse(text, settings={"PREFER_DATES_FROM": "future"})
    return date.strftime("%Y-%m-%d") if date else None

def extract_fields_with_nlp(text):
    """Extract both salary and deadline from the job posting."""
    salary = extract_salary(text)
    deadline = extract_deadline(text)
    return {
        "salary": salary,
        "deadline": deadline
    }
