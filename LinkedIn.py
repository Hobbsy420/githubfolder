# linkedin.py
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import logging
import tkinter as tk
from tkinter import messagebox
import csv

# Default config
DEFAULT_QUERY = "Software Engineer"
DEFAULT_LOCATION = "San Francisco, CA"
LINKEDIN_URL = "https://www.linkedin.com/jobs"
MAX_APPLICATIONS = 50
CSV_FILENAME = "applied_jobs.csv"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("apply_50_jobs")

def init_driver(headless=False):
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def show_alert(title, message):
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(title, message)
    root.destroy()

def wait_for_login(driver, timeout=300):
    logger.info("Waiting for user to log in to LinkedIn...")
    driver.get("https://www.linkedin.com/login")
    start_time = time.time()
    while time.time() - start_time < timeout:
        if "feed" in driver.current_url:
            logger.info("Login successful.")
            return True
        time.sleep(2)
    logger.error("Login timeout reached. Please log in manually within the timeout window.")
    show_alert("Login Timeout", "Login was not detected within the expected time.")
    return False

def search_jobs(driver, query, location):
    driver.get(LINKEDIN_URL)
    time.sleep(5)
    try:
        search_input = driver.find_element(By.CSS_SELECTOR, "input[aria-label='Search by title, skill, or company']")
        location_input = driver.find_element(By.CSS_SELECTOR, "input[aria-label='City, state, or zip code']")

        search_input.clear()
        search_input.send_keys(query)

        location_input.clear()
        location_input.send_keys(location)
        location_input.send_keys(Keys.RETURN)

        logger.info("Search submitted successfully.")
        time.sleep(5)

        html = driver.page_source
        return html
    except Exception as e:
        logger.error(f"Failed to search jobs: {e}")
        show_alert("Search Error", "An error occurred while searching for jobs.")
        return ""

def parse_job_listings(html):
    soup = BeautifulSoup(html, "html.parser")
    job_cards = soup.find_all("li", class_="jobs-search-results__list-item")

    jobs = []
    seen_urls = set()
    for card in job_cards:
        try:
            title_elem = card.find("span", class_="sr-only")
            title = title_elem.get_text(strip=True) if title_elem else "N/A"

            company_elem = card.find("a", class_="hidden-nested-link")
            company = company_elem.get_text(strip=True) if company_elem else "N/A"

            location_elem = card.find("span", class_="job-search-card__location")
            location = location_elem.get_text(strip=True) if location_elem else "N/A"

            job_url_elem = card.find("a", href=True)
            job_url = "https://www.linkedin.com" + job_url_elem['href'] if job_url_elem else "N/A"

            if job_url not in seen_urls:
                seen_urls.add(job_url)
                jobs.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "url": job_url
                })

        except Exception as e:
            logger.warning(f"Failed to parse a job card: {e}")

    logger.info(f"Parsed {len(jobs)} unique job listings.")
    return jobs

def apply_to_single_job(driver, job):
    try:
        driver.get(job['url'])
        time.sleep(3)
        easy_apply_btn = driver.find_element(By.CSS_SELECTOR, "button.jobs-apply-button")
        if "Easy Apply" in easy_apply_btn.text:
            easy_apply_btn.click()
            time.sleep(2)
            submit_btn = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Submit application']")
            submit_btn.click()
            time.sleep(2)
            logger.info(f"Applied to {job['title']} at {job['company']}")
            return True
        else:
            logger.info(f"No Easy Apply for {job['title']} at {job['company']}")
            return False
    except Exception as e:
        logger.warning(f"Could not apply to {job['title']} at {job['company']}: {e}")
        return False

def save_to_csv(applied_jobs, filename):
    try:
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=["title", "company", "location", "url"])
            writer.writeheader()
            for job in applied_jobs:
                writer.writerow(job)
        logger.info(f"Saved {len(applied_jobs)} applied jobs to {filename}.")
    except Exception as e:
        logger.error(f"Failed to write to CSV file: {e}")

def apply_to_jobs(query, location, headless):
    logger.info("Starting to apply to jobs")
    driver = init_driver(headless=headless)

    if not wait_for_login(driver):
        driver.quit()
        return

    html = search_jobs(driver, query, location)
    if html:
        jobs = parse_job_listings(html)
        applied = 0
        applied_jobs = []
        for job in jobs:
            if applied >= MAX_APPLICATIONS:
                break
            success = apply_to_single_job(driver, job)
            if success:
                applied_jobs.append(job)
                applied += 1
        save_to_csv(applied_jobs, CSV_FILENAME)
        logger.info(f"Finished. Applied to {applied} jobs.")
    else:
        logger.error("No job listings were found.")

    driver.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LinkedIn Job Apply Bot")
    parser.add_argument("--query", type=str, default=DEFAULT_QUERY, help="Job title or keywords to search")
    parser.add_argument("--location", type=str, default=DEFAULT_LOCATION, help="Location to search in")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    args = parser.parse_args()

    apply_to_jobs(args.query, args.location, args.headless)
