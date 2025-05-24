# scripts/search_jobs.py

from utils.storage import load_json, save_json
from scrapers.wellfound import get_wellfound_jobs
from scrapers.linkedin import get_linkedin_jobs

def run():
    print("🔍 [Search Jobs] Searching Wellfound...")
    existing = load_json("data/job_listings.json")
    existing_ids = {job["id"] for job in existing}

    new_jobs = get_wellfound_jobs("python")
    added = 0
    for job in new_jobs:
        if job["id"] not in existing_ids:
            existing.append(job)
            added += 1

    print("🔍 [Search Jobs] Searching LinkedIn...")
    linkedin_jobs = get_linkedin_jobs("python developer", limit=10)
    for job in linkedin_jobs:
        if job["id"] not in existing_ids:
            existing.append(job)
            added += 1

    save_json("data/job_listings.json", existing)
    print(f"✅ Added {added} new job(s) from Wellfound and LinkedIn.")
