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

    for salary in salaries:
        match = re.search(
            r"(\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(per\s*(month|year|hour|week|annum))?",
            salary, re.IGNORECASE
        )
        if match:
            return match.group(0)

    return None

def extract_deadline(text):
    """Aggressively extract the most likely deadline-related date."""
    lines = text.splitlines()
    deadline_keywords = [
        "deadline", "closing date", "apply by", "last day", "applications due",
        "filing deadline", "apply before", "closing at"
    ]

    potential_dates = []
    current_date = datetime.now()

    # Prioritize lines with keywords
    for line in lines:
        lower_line = line.lower()
        if any(keyword in lower_line for keyword in deadline_keywords):
            date = parse(line, settings={"PREFER_DATES_FROM": "future"})
            if date and date > current_date:
                potential_dates.append(date)

    # Fallback regex patterns to aggressively grab anything that looks like a date
    date_patterns = [
        r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
        r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|"
        r"Dec(?:ember)?)\s\d{1,2},\s\d{4}\b",
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        r"\b\d{4}-\d{2}-\d{2}\b"
    ]

    for pattern in date_patterns:
        for match in re.finditer(pattern, text):
            date = parse(match.group(), settings={"PREFER_DATES_FROM": "future"})
            if date and date > current_date:
                potential_dates.append(date)

    if potential_dates:
        return min(potential_dates).strftime("%Y-%m-%d")

    # Final fallback
    fallback_date = parse(text, settings={"PREFER_DATES_FROM": "future"})
    return fallback_date.strftime("%Y-%m-%d") if fallback_date and fallback_date > current_date else None

def extract_fields_with_nlp(text):
    """Extract both salary and deadline from the job posting."""
    salary = extract_salary(text)
    deadline = extract_deadline(text)
    return {
        "salary": salary,
        "deadline": deadline
    }
