import requests
from bs4 import BeautifulSoup

def scrape_jobs():
    url = "https://www.governmentjobs.com/careers/northcarolina"

    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    response = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")
    print(soup.prettify())
    
    if response.status_code == 200:
        # print("Reached the website.")
        jobs = soup.find_all('li', {'class': 'list-item'})
        print(jobs)

        
        for job in jobs:
            print(job)

        # for article in articles:
        #     title = article.find('h3', class_ = 'clamp yf-82qtw3').text
        #     link_element = article.find('a', class_='subtle-link')
        #     link = link_element.get('href')
        #     description = article.find('p', class_="clamp yf-82qtw3").text
        #     publishing_element = article.find('div', class_ = 'publishing')

        #     parts_text = publishing_element.text.strip()
        #     parts = parts_text.split("•")
        #     if len(parts) > 0:
        #         source = parts[0].strip()
        #     else:
        #         source = "Unknown Source"

        # print("Fetched the articles.")

    elif response.status_code == 404:
        print(f"404 Error -- Page not Found") 

    else:
        return None
    
print(scrape_jobs())