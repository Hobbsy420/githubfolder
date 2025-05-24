import logging
import os
from logging.handlers import TimedRotatingFileHandler

# Other imports
import time
import csv
import re
import smtplib
import datetime
import pytz
import schedule
import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from email.mime.text import MIMEText

# Setup logger
os.makedirs("logs", exist_ok=True)
logger = logging.getLogger("job_bot")
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

file_handler = TimedRotatingFileHandler(
    "logs/job_bot.log", when="midnight", interval=1, backupCount=7, encoding="utf-8"
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Silence noisy third-party logs
for noisy_logger in ["selenium", "urllib3", "requests", "schedule"]:
    logging.getLogger(noisy_logger).setLevel(logging.WARNING)

# Function to notify on error via email
def notify_admin(subject, message):
    try:
        msg = MIMEText(message)
        msg["Subject"] = subject
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = ADMIN_EMAIL
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        logger.info("Admin notified of error via email")
    except Exception as e:
        logger.error(f"Failed to notify admin: {str(e)}")

# Your existing job bot functions

def apply_to_job(job_link, cover_letter):
    logger.info(f"Attempting to apply to job: {job_link}")
    try:
        driver.get(job_link)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.jobs-apply-button")))
        apply_button = driver.find_element(By.CSS_SELECTOR, "button.jobs-apply-button")
        apply_button.click()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "textarea")))
        cover_letter_field = driver.find_element(By.CSS_SELECTOR, "textarea")
        cover_letter_field.send_keys(cover_letter)
        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        logger.info(f"Applied to job: {job_link}")
        return True
    except (TimeoutException, NoSuchElementException, WebDriverException) as e:
        logger.warning(f"Failed to apply to job {job_link}: {str(e)}")
        return False

# ... all other functions remain unchanged ...

def main():
    logger.info("Starting job bot")
    jobs = []
    applied_jobs = []
    try:
        login_to_linkedin()
        linkedin_html = search_jobs()
        jobs.extend(parse_linkedin_jobs(linkedin_html))
        indeed_html = search_indeed_jobs()
        jobs.extend(parse_indeed_jobs(indeed_html))
        wellfound_html = search_wellfound_jobs()
        jobs.extend(parse_wellfound_jobs(wellfound_html))
        filtered_jobs = filter_jobs(jobs)
        for job in filtered_jobs:
            if job[2] == "LinkedIn":
                cover_letter = generate_cover_letter(job[0])
                if apply_to_job(job[1], cover_letter):
                    applied_jobs.append(job[1])
        log_jobs_to_csv(filtered_jobs, applied_jobs)
        email_results(filtered_jobs)
        send_slack_notification(filtered_jobs, applied_jobs)
        logger.info(f"✔ Found {len(jobs)} jobs, filtered to {len(filtered_jobs)}, applied to {len(applied_jobs)}")
    except Exception as e:
        error_message = f"Main process failed: {str(e)}"
        logger.error(error_message)
        notify_admin("Job Bot Failure", error_message)
    finally:
        driver.quit()
        logger.info("WebDriver closed")

# Schedule and run loop
if __name__ == "__main__":
    logger.info("Starting bot with scheduler")
    tz = pytz.timezone("America/Los_Angeles")
    schedule.every().monday.at("09:00", tz).do(main)
    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            error_message = f"Scheduler loop failed: {str(e)}"
            logger.error(error_message)
            notify_admin("Scheduler Loop Error", error_message)
        time.sleep(60)
