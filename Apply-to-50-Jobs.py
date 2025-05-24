import os
import pandas as pd
from odf import opendocument, table, text
from datetime import datetime
import time
import random
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import tkinter as tk
from tkinter import messagebox, ttk

# Define paths
documents_folder = r"C:\Users\HP\Documents\Job Tracker spreadsheet (JTS)"
input_tracker = os.path.join(documents_folder, "Job_Tracker.ods")
output_tracker = os.path.join(documents_folder, "Apply_to_50_Jobs.ods")
cover_letter_folder = os.path.join(documents_folder, "Cover_Letters")

# Define columns for the tracker
columns = ["Date", "Company", "Position", "Status", "Link", "Notes", "Cover_Letter_Path"]

# Function to read .ods file
def read_ods(file_path):
    print(f"Attempting to read {file_path}")
    try:
        df = pd.read_excel(file_path, engine='odf')
        print(f"Successfully read {file_path} with {len(df)} entries")
        return df
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return pd.DataFrame(columns=columns)

# Function to write to .ods file
def write_ods(df, file_path):
    print(f"Attempting to write to {file_path}")
    try:
        df.to_excel(file_path, engine='odf', index=False)
        print(f"Tracker saved to {file_path}")
    except Exception as e:
        print(f"Error writing to {file_path}: {e}")

# Function to call xAI Grok 3 API for cover letter generation
def generate_ai_cover_letter(company, position, user_skills, api_key):
    print(f"Generating cover letter for {position} at {company}")
    try:
        url = "https://api.x.ai/v1/grok/generate"  # Placeholder xAI API endpoint
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        prompt = f"""Generate a professional cover letter for a {position} position at {company}. 
        Highlight my skills in {user_skills}. Keep it concise, under 200 words, and address it to 'Hiring Manager'."""
        payload = {
            "model": "grok-3",
            "prompt": prompt,
            "max_tokens": 300
        }
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        cover_letter = response.json().get("choices", [{}])[0].get("text", "")
        if not cover_letter:
            raise ValueError("Empty response from API")
        print(f"API-generated cover letter for {company}")
        return cover_letter.strip()
    except Exception as e:
        print(f"API error for {company}: {e}. Using fallback template.")
        return f"""Dear Hiring Manager,

I am excited to apply for the {position} position at {company}. With my skills in {user_skills}, I am confident in my ability to contribute to your team. [Add specific details about your experience].

Sincerely,
[Your Name]"""

# Function to initialize Selenium WebDriver
def init_driver():
    print("Initializing Chrome WebDriver")
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(options=chrome_options)
    return driver

# Function to perform manual LinkedIn login
def manual_login(driver):
    print("Navigating to LinkedIn login page")
    driver.get("https://www.linkedin.com/login")
    print("Please log in to LinkedIn manually in the browser, then press Enter in the console to continue...")
    input("Press Enter when logged in: ")
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "global-nav__me"))
        )
        print("Login successful!")
        return True
    except TimeoutException:
        print("Login failed or took too long. Please try again.")
        return False

# Function to apply to LinkedIn jobs
def apply_to_jobs(driver, target_jobs=5, user_skills="Python, JavaScript, Data Analysis", api_key=None, excluded_companies=["FusionTek", "PCs for People"]):
    jobs_applied = 0
    page = 1
    job_data = []
    
    # Load existing tracker
    if os.path.exists(input_tracker):
        df = read_ods(input_tracker)
    else:
        print("No existing Job Tracker found. Starting fresh.")
        df = pd.DataFrame(columns=columns)
    
    to_apply = df[df['Status'].str.contains("To Apply", case=False, na=False)] if not df.empty else pd.DataFrame(columns=columns)
    current_count = len(to_apply)
    print(f"Found {current_count} jobs marked 'To Apply' in existing tracker.")
    
    if current_count >= target_jobs:
        print("Enough jobs already marked 'To Apply'. Using existing entries.")
        return to_apply.head(target_jobs)
    
    # Search for jobs
    print("Navigating to LinkedIn Easy Apply job search")
    driver.get("https://www.linkedin.com/jobs/search/?f_AL=true")
    time.sleep(random.uniform(2, 5))
    
    while jobs_applied + current_count < target_jobs:
        try:
            # Scroll to load all jobs on the page
            jobs_list = driver.find_elements(By.CSS_SELECTOR, ".job-card-container--clickable")
            print(f"Found {len(jobs_list)} jobs on page {page}")
            for job in jobs_list:
                if jobs_applied + current_count >= target_jobs:
                    break
                
                driver.execute_script("arguments[0].scrollIntoView();", job)
                time.sleep(random.uniform(1, 3))
                job.click()
                time.sleep(random.uniform(2, 4))
                
                # Extract job details
                try:
                    company = driver.find_element(By.CSS_SELECTOR, ".jobs-unified-top-card__company-name").text.strip()
                    if any(excluded.lower() in company.lower() for excluded in excluded_companies):
                        print(f"Skipping excluded company: {company}")
                        continue
                    position = driver.find_element(By.CSS_SELECTOR, ".jobs-unified-top-card__job-title").text.strip()
                    link = driver.current_url
                except NoSuchElementException:
                    print("Could not extract job details. Skipping.")
                    continue
                
                # Check for Easy Apply
                try:
                    apply_button = driver.find_element(By.CSS_SELECTOR, ".jobs-apply-button--top-card")
                    if apply_button.text != "Easy Apply":
                        print(f"Job at {company} is not Easy Apply. Skipping.")
                        continue
                except NoSuchElementException:
                    print(f"No apply button found for {company}. Skipping.")
                    continue
                
                # Apply to job
                try:
                    apply_button.click()
                    time.sleep(random.uniform(2, 5))
                    submit_button = driver.find_element(By.CSS_SELECTOR, "[aria-label='Submit application']")
                    submit_button.click()
                    time.sleep(random.uniform(2, 5))
                    
                    # Generate and save cover letter
                    os.makedirs(cover_letter_folder, exist_ok=True)
                    cover_letter = generate_ai_cover_letter(company, position, user_skills, api_key)
                    cover_letter_path = os.path.join(cover_letter_folder, f"Cover_Letter_{company}_{position}.txt")
                    with open(cover_letter_path, 'w', encoding='utf-8') as f:
                        f.write(cover_letter)
                    print(f"Saved cover letter to {cover_letter_path}")
                    
                    # Log job details
                    job_entry = {
                        "Date": datetime.now().strftime("%Y-%m-%d"),
                        "Company": company,
                        "Position": position,
                        "Status": "Applied",
                        "Link": link,
                        "Notes": "Applied via automation (test run)",
                        "Cover_Letter_Path": cover_letter_path
                    }
                    job_data.append(job_entry)
                    jobs_applied += 1
                    print(f"Applied to {position} at {company}. Total applied: {jobs_applied + current_count}")
                except NoSuchElementException:
                    print(f"Could not submit application for {company}. Skipping.")
                    try:
                        close_button = driver.find_element(By.CSS_SELECTOR, ".artdeco-modal__dismiss")
                        close_button.click()
                        time.sleep(random.uniform(1, 3))
                    except:
                        pass
                time.sleep(random.uniform(3, 6))  # Random delay to mimic human behavior
            
            # Move to next page
            page += 1
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, f"[aria-label='Page {page}']")
                print(f"Moving to page {page}")
                next_button.click()
                time.sleep(random.uniform(3, 7))
            except NoSuchElementException:
                print("No more pages to load. Stopping.")
                break
        
        except Exception as e:
            print(f"Error on page {page}: {e}")
            break
    
    # Combine new and existing jobs
    new_df = pd.DataFrame(job_data, columns=columns)
    final_df = pd.concat([to_apply, new_df], ignore_index=True).head(target_jobs)
    write_ods(final_df, output_tracker)
    print(f"Test run complete. Applied to {jobs_applied} new jobs.")
    return final_df

# Function to create GUI for one-click application
def create_gui():
    root = tk.Tk()
    root.title("Test Apply to 5 Jobs")
    root.geometry("400x250")
    
    def start_applications():
        api_key = api_key_entry.get()
        user_skills = skills_entry.get()
        if not api_key:
            messagebox.showerror("Error", "Please enter an API key.")
            return
        if not user_skills:
            user_skills = "Python, JavaScript, Data Analysis"  # Default skills
        print(f"Starting test run with skills: {user_skills}")
        driver = init_driver()
        if manual_login(driver):
            apply_to_jobs(driver, target_jobs=5, user_skills=user_skills, api_key=api_key)
            driver.quit()
        else:
            messagebox.showerror("Error", "Login failed. Please try again.")
        root.destroy()
    
    # GUI elements
    tk.Label(root, text="Enter your xAI API Key:").pack(pady=10)
    api_key_entry = tk.Entry(root, width=40, show="*")
    api_key_entry.pack(pady=5)
    
    tk.Label(root, text="Enter your skills (comma-separated, e.g., Python, JavaScript):").pack(pady=10)
    skills_entry = tk.Entry(root, width=40)
    skills_entry.pack(pady=5)
    
    apply_button = tk.Button(root, text="Test Apply to 5 Jobs", command=start_applications)
    apply_button.pack(pady=20)
    
    root.mainloop()

# Main logic
if __name__ == "__main__":
    print("Starting LinkedIn job application test run...")
    create_gui()