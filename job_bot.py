import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText

# Load environment variables
load_dotenv()

LINKEDIN_USERNAME = os.getenv("LINKEDIN_USERNAME")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

# Set up Chrome WebDriver
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in background
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def login_to_linkedin():
    driver.get("https://www.linkedin.com/login")
    time.sleep(2)

    username_input = driver.find_element(By.ID, "username")
    password_input = driver.find_element(By.ID, "password")
    username_input.send_keys(LINKEDIN_USERNAME)
    password_input.send_keys(LINKEDIN_PASSWORD)
    password_input.send_keys(Keys.RETURN)
    time.sleep(3)

def search_jobs(query="Software Engineer", location="Remote"):
    driver.get("https://www.linkedin.com/jobs")
    time.sleep(3)

    search_keyword = driver.find_element(By.CSS_SELECTOR, "input[aria-label='Search jobs']")
    search_location = driver.find_element(By.CSS_SELECTOR, "input[aria-label='Search location']")

    search_keyword.clear()
    search_keyword.send_keys(query)
    search_location.clear()
    search_location.send_keys(location)
    search_location.send_keys(Keys.RETURN)

    time.sleep(5)
    return driver.page_source

def parse_jobs(page_html):
    soup = BeautifulSoup(page_html, "html.parser")
    job_elements = soup.find_all("li", class_="jobs-search-results__list-item")

    jobs = []
    for job in job_elements:
        title_elem = job.find("span", class_="screen-reader-text")
        link_elem = job.find("a", href=True)
        if title_elem and link_elem:
            jobs.append((title_elem.get_text(strip=True), f"https://www.linkedin.com{link_elem['href']}"))

    return jobs

def email_results(jobs):
    if not jobs:
        return

    body = "\n\n".join([f"{title}\n{link}" for title, link in jobs])
    msg = MIMEText(body)
    msg["Subject"] = "Weekly Job Listings"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = RECIPIENT_EMAIL

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

def main():
    login_to_linkedin()
    html = search_jobs()
    jobs = parse_jobs(html)
    email_results(jobs)
    print(f"✔ Found and emailed {len(jobs)} jobs.")
    driver.quit()

if __name__ == "__main__":
    main()