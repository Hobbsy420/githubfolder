# ... (Previous imports and code unchanged until parse_wellfound_jobs)

def apply_to_job(job_link, cover_letter):
    logger.info(f"Attempting to apply to job: {job_link}")
    try:
        driver.get(job_link)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.jobs-apply-button")))
        apply_button = driver.find_element(By.CSS_SELECTOR, "button.jobs-apply-button")
        apply_button.click()
        # Assume simple form with cover letter field
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

def filter_jobs(jobs, include_keywords=None, exclude_keywords=None):
    logger.info("Filtering jobs")
    include_keywords = include_keywords or ["Python", "Junior", "Entry Level"]
    exclude_keywords = exclude_keywords or ["Senior", "Lead", "Principal"]
    filtered_jobs = []
    for job in jobs:
        title = job[0].lower()
        if (any(kw.lower() in title for kw in include_keywords) and
            not any(kw.lower() in title for kw in exclude_keywords)):
            filtered_jobs.append(job)
        else:
            logger.info(f"Filtered out job: {job[0]}")
    logger.info(f"Filtered to {len(filtered_jobs)} jobs")
    return filtered_jobs

def generate_cover_letter(job_title):
    logger.info(f"Generating cover letter for {job_title}")
    try:
        sanitized_title = re.sub(r'[^\x00-\x7F]+', '', job_title)
        template = f"""
Dear Hiring Manager,

I am excited to apply for the {sanitized_title} position. With my expertise in {USER_SKILLS}, I am confident in my ability to contribute to your team. My experience includes developing scalable applications, collaborating in agile environments, and solving complex technical challenges.

I am particularly drawn to this role because of its focus on innovative solutions. I look forward to bringing my skills and passion to your organization.

Thank you for considering my application.

Sincerely,
{USER_NAME}
"""
        return template.strip()
    except Exception as e:
        logger.error(f"Error generating cover letter: {str(e)}")
        return ""

def log_jobs_to_csv(jobs, applied_jobs=None):
    logger.info("Logging jobs to CSV")
    applied_jobs = applied_jobs or []
    try:
        file_exists = os.path.isfile("submitted_jobs.csv")
        with open("submitted_jobs.csv", "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Timestamp", "Job Title", "Link", "Source", "Cover Letter", "Applied"])
            for job in jobs:
                timestamp = datetime.datetime.now().isoformat()
                sanitized_title = re.sub(r'[^\x00-\x7F]+', '', job[0])
                cover_letter = generate_cover_letter(job[0])
                applied = "Yes" if job[1] in applied_jobs else "No"
                writer.writerow([timestamp, sanitized_title, job[1], job[2], cover_letter, applied])
        logger.info("Jobs logged to submitted_jobs.csv")
    except Exception as e:
        logger.error(f"Error logging jobs to CSV: {str(e)}")

def email_results(jobs):
    if not jobs:
        logger.info("No jobs to email")
        return
    try:
        body = "\n\n".join([f"{title}\n{link} ({source})" for title, link, source in jobs])
        msg = MIMEText(body)
        msg["Subject"] = "Weekly Job Listings from Job Bot"
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = RECIPIENT_EMAIL
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        logger.info("Email sent successfully")
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")

def send_slack_notification(jobs, applied_jobs=None):
    applied_jobs = applied_jobs or []
    if not jobs or not SLACK_WEBHOOK_URL:
        logger.info("No jobs or Slack webhook URL, skipping notification")
        return
    for attempt in range(3):
        try:
            message = f"Found {len(jobs)} jobs (applied to {len(applied_jobs)}):\n" + \
                      "\n".join([f"- {title} ({source}): {link} {'[Applied]' if link in applied_jobs else ''}" for title, link, source in jobs])
            payload = {"text": message}
            response = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info("Slack notification sent successfully")
                return
            else:
                logger.warning(f"Slack notification attempt {attempt + 1} failed: {response.text}")
        except Exception as e:
            logger.warning(f"Slack notification attempt {attempt + 1} failed: {str(e)}")
        time.sleep(5)
    logger.error("Failed to send Slack notification after 3 attempts")

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
        # Filter jobs
        filtered_jobs = filter_jobs(jobs)
        # Apply to LinkedIn jobs with Easy Apply
        for job in filtered_jobs:
            if job[2] == "LinkedIn":  # Only apply to LinkedIn jobs
                cover_letter = generate_cover_letter(job[0])
                if apply_to_job(job[1], cover_letter):
                    applied_jobs.append(job[1])
        log_jobs_to_csv(filtered_jobs, applied_jobs)
        email_results(filtered_jobs)
        send_slack_notification(filtered_jobs, applied_jobs)
        logger.info(f"✔ Found {len(jobs)} jobs, filtered to {len(filtered_jobs)}, applied to {len(applied_jobs)}")
    except Exception as e:
        logger.error(f"Main process failed: {str(e)}")
    finally:
        driver.quit()
        logger.info("WebDriver closed")

def run_job_bot():
    main()

if __name__ == "__main__":
    logger.info("Starting bot with scheduler")
    tz = pytz.timezone("America/Los_Angeles")
    schedule.every().monday.at("09:00", tz).do(run_job_bot)
    while True:
        schedule.run_pending()
        time.sleep(60)