
# Job Application Bot

This bot automates job searches and applications across LinkedIn, Indeed, and Wellfound. It scrapes job listings, generates cover letters, logs submissions, and can send weekly reports via email.

## Features

- **Multi-platform scraping**: LinkedIn, Indeed, and Wellfound
- **Automated login**: Logs into LinkedIn to fetch job listings
- **Cover letter generation**: Uses a custom module to personalize applications
- **Email notifications**: Sends a weekly summary of applications
- **Scheduler**: Runs every Monday at 9:00 AM by default
- **Logging**: Saves application data to `submitted_jobs.csv`

## Installation

1. Clone the repo or extract the ZIP archive.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Update credentials in `job_bot.py`:
   - LinkedIn username and password
   - Email credentials for notifications

4. (Optional) Update your job title and location in `run_job_bot()`.

## Running

```bash
python job_bot.py
```

This will start the scheduled job bot which runs weekly.

To run immediately:

```bash
from job_bot import run_job_bot
run_job_bot()
```

## Notes

- You need Chrome installed for Selenium to work.
- The bot uses `webdriver-manager` to auto-install ChromeDriver.
- Consider running in headless mode for production.

---

## License

MIT License.
