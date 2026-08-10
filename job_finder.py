import os
import sys
import json
import re
import datetime
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

# User Profile Configuration
PROFILE_NAME = "Sagar Sohrab"
TARGET_YOE_MIN = 1
TARGET_YOE_MAX = 3
TARGET_ROLES = [
    "Business Analyst",
    "Data Analyst",
    "Product Analyst",
    "Analytics Engineer",
    "Data Analytics Specialist",
    "Operations Analyst"
]
EXCLUDE_TITLE_TERMS = [
    "director", "vp", "vice president", "head of", "principal", 
    "lead analyst", "staff analyst", "senior manager", "10+ years", "8+ years", "7+ years",
    "salary", "guide", "how to", "tips", "course", "certification", "career", "interview questions",
    "making", "make?", "vs", "overview", "roadmap", "turns to reddit", "reddit"
]
EXCLUDE_NEWS_SOURCES = [
    "livemint.com", "moneycontrol", "timesofindia", "economic times", "hindustantimes", 
    "gadgets360", "ndtv", "quora", "reddit", "medium.com", "towardsdatascience"
]
EXCLUDE_LOCATION_TERMS = [
    "usa", "us only", "latam", "mexico", "canada", "uk only", "europe only", "germany", "france"
]
TARGET_LOCATIONS = ["bengaluru", "bangalore", "mumbai", "remote", "india", "worldwide", "anywhere"]
SKILL_KEYWORDS = [
    "sql", "bigquery", "postgresql", "mysql", "python", "pandas", "numpy",
    "scipy", "tableau", "power bi", "streamlit", "etl", "funnel", "a/b testing",
    "anomaly detection", "z-score", "fintech", "payments", "gcp"
]

def calculate_relevance_score(title, description, location, company=""):
    score = 0
    title_lower = title.lower()
    desc_lower = description.lower()
    loc_lower = location.lower()
    comp_lower = company.lower()
    full_text = f"{title_lower} {desc_lower}"

    # 1. Filter out Articles, News Sites, Blogs, & Reddit Posts
    for bad_source in EXCLUDE_NEWS_SOURCES:
        if bad_source in comp_lower or bad_source in title_lower or bad_source in desc_lower:
            return 0, []

    for bad_term in EXCLUDE_TITLE_TERMS:
        if bad_term in title_lower:
            return 0, []

    # 2. Filter out Non-India / Non-Worldwide Locations (e.g. US Only, LATAM, Mexico)
    for bad_loc in EXCLUDE_LOCATION_TERMS:
        if bad_loc in loc_lower:
            return 0, []

    # Check that location is India or Worldwide Remote
    loc_valid = any(loc in loc_lower for loc in TARGET_LOCATIONS)
    if not loc_valid:
        return 0, []

    # Boost for Junior / Mid / Associate roles (1-3 YOE)
    if any(term in title_lower for term in ["junior", "associate", "analyst i", "analyst ii", "mid"]):
        score += 15

    # Check YOE mentions in description
    yoe_matches = re.findall(r'(\d+)\+?\s*(?:-\s*(\d+)\+?)?\s*(?:years|yoe|yrs)', full_text)
    for min_y, max_y in yoe_matches:
        try:
            min_val = int(min_y)
            if min_val > 5:
                return 0, [] # Exclude 6+ years required
            elif 1 <= min_val <= 3:
                score += 20
        except ValueError:
            pass

    # 3. Title match
    for role in TARGET_ROLES:
        if role.lower() in title_lower:
            score += 35
            break

    # 4. Location match bonus
    if "bengaluru" in loc_lower or "bangalore" in loc_lower or "mumbai" in loc_lower or "india" in loc_lower:
        score += 25
    elif "worldwide" in loc_lower or "anywhere" in loc_lower:
        score += 15

    # 5. Skill keywords match
    matched_skills = []
    for skill in SKILL_KEYWORDS:
        if re.search(r'\b' + re.escape(skill) + r'\b', title_lower) or re.search(r'\b' + re.escape(skill) + r'\b', desc_lower):
            score += 10
            matched_skills.append(skill)

    # 6. Freshness Boost (First to apply advantage)
    if any(fresh in desc_lower for fresh in ["hour", "hours", "minute", "minutes", "just posted", "today", "1 day"]):
        score += 20  # +20 pts boost for brand new postings!

    return score, list(set(matched_skills))

def fetch_remotive_jobs():
    jobs = []
    try:
        url = "https://remotive.com/api/remote-jobs?category=data"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            for item in data.get("jobs", []):
                jobs.append({
                    "title": item.get("title", ""),
                    "company": item.get("company_name", ""),
                    "location": item.get("candidate_required_location", "Remote"),
                    "url": item.get("url", ""),
                    "source": "Remotive",
                    "date": item.get("publication_date", "")[:10],
                    "description": BeautifulSoup(item.get("description", ""), "html.parser").get_text()[:500]
                })
    except Exception as e:
        print(f"Error fetching Remotive jobs: {e}")
    return jobs

def fetch_arbeitnow_jobs():
    jobs = []
    try:
        url = "https://www.arbeitnow.com/api/job-board-api"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            for item in data.get("data", []):
                jobs.append({
                    "title": item.get("title", ""),
                    "company": item.get("company_name", ""),
                    "location": item.get("location", "Remote/Global"),
                    "url": item.get("url", ""),
                    "source": "Arbeitnow",
                    "date": datetime.date.today().isoformat(),
                    "description": BeautifulSoup(item.get("description", ""), "html.parser").get_text()[:500]
                })
    except Exception as e:
        print(f"Error fetching Arbeitnow jobs: {e}")
    return jobs

def fetch_jobicy_jobs():
    jobs = []
    try:
        url = "https://jobicy.com/api/v2/remote-jobs?count=20&industry=data-science"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            for item in data.get("jobs", []):
                jobs.append({
                    "title": item.get("jobTitle", ""),
                    "company": item.get("companyName", ""),
                    "location": item.get("jobGeo", "Remote"),
                    "url": item.get("url", ""),
                    "source": "Jobicy",
                    "date": item.get("pubDate", "")[:10] if item.get("pubDate") else datetime.date.today().isoformat(),
                    "description": item.get("jobExcerpt", "")[:500]
                })
    except Exception as e:
        print(f"Error fetching Jobicy jobs: {e}")
    return jobs

def fetch_linkedin_jobs():
    jobs = []
    queries = [
        ("Business Analyst", "Bengaluru, Karnataka, India"),
        ("Data Analyst", "Bengaluru, Karnataka, India"),
        ("Product Analyst", "Mumbai, Maharashtra, India"),
        ("Analytics Engineer", "India")
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for keyword, location in queries:
        try:
            url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={quote_plus(keyword)}&location={quote_plus(location)}&start=0"
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                soup = BeautifulSoup(res.content, "html.parser")
                cards = soup.find_all("li")
                for card in cards[:6]:
                    title_elem = card.find("h3", class_="base-search-card__title")
                    comp_elem = card.find("h4", class_="base-search-card__subtitle")
                    loc_elem = card.find("span", class_="job-search-card__location")
                    link_elem = card.find("a", class_="base-card__full-link")

                    title = title_elem.text.strip() if title_elem else ""
                    company = comp_elem.text.strip() if comp_elem else "Tech Company"
                    loc = loc_elem.text.strip() if loc_elem else location
                    job_url = link_elem["href"] if link_elem and "href" in link_elem.attrs else ""

                    # Extract relative posting time (e.g. 2 hours ago, 1 day ago)
                    time_elem = card.find("time")
                    posted_time = time_elem.text.strip() if time_elem else "Recently"

                    if title and job_url:
                        jobs.append({
                            "title": title,
                            "company": company,
                            "location": loc,
                            "url": job_url.split("?")[0],  # Clean tracking params
                            "source": "LinkedIn Jobs",
                            "date": posted_time,
                            "description": f"{title} at {company} in {loc}. Posted {posted_time}."
                        })
        except Exception as e:
            print(f"Error fetching LinkedIn jobs for '{keyword}': {e}")

    return jobs

def fetch_greenhouse_lever_jobs():
    jobs = []
    queries = [
        'site:boards.greenhouse.io "Business Analyst" Bengaluru OR Bangalore',
        'site:jobs.lever.co "Data Analyst" India',
        'site:myworkdayjobs.com "Product Analyst" Bangalore OR Mumbai'
    ]
    for q in queries:
        try:
            rss_url = f"https://news.google.com/rss/search?q={quote_plus(q)}&hl=en-IN&gl=IN&ceid=IN:en"
            res = requests.get(rss_url, timeout=10)
            if res.status_code == 200:
                soup = BeautifulSoup(res.content, "xml")
                for item in soup.find_all("item")[:5]:
                    title = item.find("title").get_text() if item.find("title") else ""
                    link = item.find("link").get_text() if item.find("link") else ""
                    source_name = item.find("source").get_text() if item.find("source") else "Company Career Site"

                    if "greenhouse" in link.lower() or "lever" in link.lower() or "workday" in link.lower():
                        jobs.append({
                            "title": title.split(" - ")[0] if " - " in title else title,
                            "company": source_name,
                            "location": "Bengaluru / Mumbai / India",
                            "url": link,
                            "source": "Direct Company ATS (Greenhouse/Lever)",
                            "date": datetime.date.today().isoformat(),
                            "description": title
                        })
        except Exception as e:
            print(f"Error fetching ATS jobs for '{q}': {e}")
    return jobs

def run_job_search():
    print("Starting automated job search...")
    all_raw_jobs = []
    all_raw_jobs.extend(fetch_linkedin_jobs())
    all_raw_jobs.extend(fetch_greenhouse_lever_jobs())
    all_raw_jobs.extend(fetch_remotive_jobs())
    all_raw_jobs.extend(fetch_arbeitnow_jobs())
    all_raw_jobs.extend(fetch_jobicy_jobs())

    processed_jobs = []
    seen = set()

    for job in all_raw_jobs:
        key = (job["title"].lower(), job["company"].lower())
        if key in seen:
            continue
        seen.add(key)

        score, matched_skills = calculate_relevance_score(job["title"], job["description"], job["location"], job["company"])
        if score >= 30:  # Relevance threshold
            job["relevance_score"] = score
            job["matched_skills"] = matched_skills
            processed_jobs.append(job)

    # Sort by relevance score descending
    processed_jobs.sort(key=lambda x: x["relevance_score"], reverse=True)
    return processed_jobs[:15]

def extract_ctc_information(title, description):
    text = f"{title} {description}"
    
    # Check for LPA / Lakhs pattern (e.g., 12 - 18 LPA, 15LPA, 10-15 Lacs)
    lpa_match = re.search(r'(?:₹|INR|\b)\s*(\d+\.?\d*)\s*(?:-\s*(\d+\.?\d*))?\s*(?:LPA|L|Lacs|Lakhs|Lac|Lakh)\b', text, re.IGNORECASE)
    if lpa_match:
        min_sal = lpa_match.group(1)
        max_sal = lpa_match.group(2)
        if max_sal:
            return f"₹{min_sal}L - ₹{max_sal}L PA (Listed)"
        return f"₹{min_sal}L PA (Listed)"

    # Check for USD / k salary (e.g., $80k - $120k, 90k USD)
    usd_match = re.search(r'\$\s*(\d+k?)\s*(?:-\s*\$?\s*(\d+k?))?\s*(?:/yr|/year|USD|annual)?\b', text, re.IGNORECASE)
    if usd_match:
        min_sal = usd_match.group(1)
        max_sal = usd_match.group(2)
        if max_sal:
            return f"${min_sal} - ${max_sal}/yr (Listed)"
        return f"${min_sal}/yr (Listed)"

    # Monthly salary check (e.g., ₹25,000 - ₹40,000 /month)
    month_match = re.search(r'₹?\s*(\d{2,3},?\d{3})\s*(?:-\s*₹?\s*(\d{2,3},?\d{3}))?\s*/\s*(?:month|mo|pm)\b', text, re.IGNORECASE)
    if month_match:
        min_sal = month_match.group(1)
        max_sal = month_match.group(2)
        if max_sal:
            return f"₹{min_sal} - ₹{max_sal}/mo (Listed)"
        return f"₹{min_sal}/mo (Listed)"

    # Estimated Benchmark Fallback for 1-3 YOE BA/DA/PA Roles in India
    return "₹8L - ₹18L PA (Est. 1-3 YOE Market Range)"

def generate_markdown_report(jobs):
    today = datetime.date.today().strftime("%B %d, %Y")
    md = f"# 🎯 Daily Job Digest & Application Copilot for {PROFILE_NAME}\n"
    md += f"**Date:** {today} | **Top Mid-Level Matches (1-3 YOE):** {len(jobs)}\n\n"
    md += "---\n\n"

    if not jobs:
        md += "No high-confidence 1-3 YOE matching roles found today. Check back tomorrow!\n"
        return md

    for idx, job in enumerate(jobs, 1):
        skills_str = ", ".join([f"`{s}`" for s in job["matched_skills"]]) if job["matched_skills"] else "General Analytics"
        ctc_str = extract_ctc_information(job["title"], job["description"])

        date_raw = job['date']
        is_fresh = any(kw in date_raw.lower() for kw in ["hour", "minute", "just posted", "today", "1 day", "2 day", "3 day"])
        posted_display = f"⚡ `{date_raw}` *(Early Applicant Advantage)*" if is_fresh else f"`{date_raw}`"

        md += f"### {idx}. [{job['title']}]({job['url']})\n"
        md += f"- **Company:** {job['company']}\n"
        md += f"- **Location:** {job['location']}\n"
        md += f"- **Source:** {job['source']} | **Posted:** {posted_display}\n"
        md += f"- **CTC / Compensation:** 💰 `{ctc_str}`\n"
        md += f"- **Relevance Score:** ⭐ `{job['relevance_score']} pts`\n"
        md += f"- **Matched Core Skills:** {skills_str}\n"
        md += f"- **Direct Apply Link:** 🚀 [{job['url']}]({job['url']})\n"
        
        # Tailored Resume Strategy Advice
        md += f"- 💡 **Tailored Resume Pitch Focus:**\n"
        if "sql" in job["matched_skills"] or "bigquery" in job["matched_skills"]:
            md += f"  > *Emphasize Razorpay BigQuery/PostgreSQL CTEs & window functions ($500M+ GMV).* \n"
        if "funnel" in job["matched_skills"] or "a/b testing" in job["matched_skills"]:
            md += f"  > *Highlight Meta & Airbnb checkout funnel optimization (+15% SR lift).* \n"
        if "tableau" in job["matched_skills"] or "power bi" in job["matched_skills"]:
            md += f"  > *Highlight executive dashboarding & KPI readouts in Tableau/Power BI for 15+ Tier-1 accounts.* \n"
        if "anomaly detection" in job["matched_skills"] or "python" in job["matched_skills"]:
            md += f"  > *Highlight Z-score statistical anomaly modeling & automated Python ETL latency reduction (10x latency drop).* \n"
        if not job["matched_skills"]:
            md += f"  > *Emphasize 1+ year Business Analyst experience at Razorpay driving GMV growth and automated analytics.* \n"

        if job["description"]:
            clean_desc = job["description"].replace("\n", " ").strip()
            md += f"- **Snippet:** *{clean_desc[:220]}...*\n"
        md += "\n"

    md += "---\n"
    md += "*Generated automatically by GitHub Actions Job Agent & Resume Copilot*\n"
    return md

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_email_digest(report_md, smtp_user, smtp_pass, recipient_email):
    try:
        msg = MIMEMultipart("alternative")
        today_str = datetime.date.today().strftime("%B %d, %Y")
        msg["Subject"] = f"🎯 Daily Job Digest & Resume Copilot - {today_str}"
        msg["From"] = smtp_user
        msg["To"] = recipient_email

        # Convert markdown to basic HTML for email formatting
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 650px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 8px;">🎯 Daily Job Digest for {PROFILE_NAME}</h2>
            <p style="color: #7f8c8d; font-size: 14px;">Date: {today_str} | Target: 1-3 YOE Business/Data Analyst Roles</p>
            <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
        """

        lines = report_md.split("\n")
        in_job = False
        for line in lines:
            if line.startswith("### "):
                if in_job:
                    html_body += "</div><br>"
                in_job = True
                html_body += "<div style='background: #f8f9fa; border-left: 4px solid #3498db; padding: 15px; border-radius: 4px; margin-bottom: 15px;'>"
                # Extract link and title
                match = re.search(r'### \d+\. \[(.*?)\]\((.*?)\)', line)
                if match:
                    title, url = match.group(1), match.group(2)
                    html_body += f"<h3 style='margin-top:0; color: #2980b9;'><a href='{url}' style='color: #2980b9; text-decoration: none;'>{title}</a></h3>"
                else:
                    html_body += f"<h3>{line[4:]}</h3>"
            elif line.startswith("- **Company:**"):
                html_body += f"<p style='margin: 4px 0;'><strong>Company:</strong> {line.replace('- **Company:**', '').strip()}</p>"
            elif line.startswith("- **Location:**"):
                html_body += f"<p style='margin: 4px 0;'><strong>Location:</strong> {line.replace('- **Location:**', '').strip()}</p>"
            elif line.startswith("- **CTC / Compensation:**"):
                html_body += f"<p style='margin: 4px 0;'><strong>CTC / Compensation:</strong> <span style='background: #eef9ff; color: #0077b5; padding: 2px 8px; border-radius: 3px; font-weight: bold;'>{line.replace('- **CTC / Compensation:**', '').strip()}</span></p>"
            elif line.startswith("- **Relevance Score:**"):
                html_body += f"<p style='margin: 4px 0;'><strong>Relevance Score:</strong> <span style='background: #e8f8f5; color: #27ae60; padding: 2px 8px; border-radius: 3px; font-weight: bold;'>{line.replace('- **Relevance Score:**', '').strip()}</span></p>"
            elif line.startswith("- **Matched Core Skills:**"):
                html_body += f"<p style='margin: 4px 0;'><strong>Matched Skills:</strong> {line.replace('- **Matched Core Skills:**', '').strip()}</p>"
            elif line.startswith("- **Direct Apply Link:**"):
                apply_url = re.search(r'\[(.*?)\]\((.*?)\)', line)
                if apply_url:
                    target_link = apply_url.group(2)
                    html_body += f"<div style='margin-top: 10px; margin-bottom: 8px;'><a href='{target_link}' target='_blank' style='background-color: #27ae60; color: #ffffff; padding: 8px 16px; text-decoration: none; border-radius: 4px; font-weight: bold; display: inline-block; font-size: 13px;'>🚀 Click Here to Apply Now</a></div>"
            elif "Tailored Resume Pitch Focus:" in line or line.strip().startswith("> *"):
                clean_pitch = line.replace("- 💡 **Tailored Resume Pitch Focus:**", "").replace("> *", "").replace("*", "").strip()
                if clean_pitch:
                    html_body += f"<div style='background: #fff8e1; border-left: 3px solid #f39c12; padding: 8px 12px; margin: 8px 0; font-size: 13px;'>💡 <strong>Tailored Resume Focus:</strong> {clean_pitch}</div>"
            elif line.startswith("- **Snippet:**"):
                html_body += f"<p style='margin: 4px 0; color: #555; font-size: 13px;'><em>{line.replace('- **Snippet:**', '').strip()}</em></p>"

        if in_job:
            html_body += "</div>"

        html_body += """
            <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="font-size: 12px; color: #95a5a6; text-align: center;">Generated automatically by GitHub Actions Job Agent for Sagar Sohrab</p>
          </body>
        </html>
        """

        part_plain = MIMEText(report_md, "plain")
        part_html = MIMEText(html_body, "html")
        msg.attach(part_plain)
        msg.attach(part_html)

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, recipient_email, msg.as_string())
        server.quit()
        print(f"Email digest sent successfully to {recipient_email}!")
    except Exception as e:
        print(f"Failed to send email digest: {e}")

def main():
    top_jobs = run_job_search()
    
    # Enrich job data for Web UI
    for job in top_jobs:
        job["ctc"] = extract_ctc_information(job["title"], job["description"])
        company_clean = quote_plus(job["company"])
        job["recruiter_search_url"] = f"https://www.linkedin.com/search/results/people/?keywords={company_clean}%20recruiter%20OR%20analytics%20lead"
        
        # Auto-generate custom 3-paragraph cover letter pitch
        skills_str = ", ".join(job["matched_skills"]) if job["matched_skills"] else "SQL, Python, Business Analytics"
        job["cover_letter"] = (
            f"Dear Hiring Team at {job['company']},\n\n"
            f"I am writing to express my strong interest in the {job['title']} role. With over a year of experience as a Business Analyst at Razorpay driving GMV growth and funnel optimization across 15+ Tier-1 enterprise accounts ($500M+ global GMV), I have delivered tangible ROI through advanced data analytics.\n\n"
            f"In my current position, I led checkout funnel analytics for clients like Meta and Airbnb, driving a +15% Success Rate (SR) lift, authored complex SQL transformations on GCP BigQuery/PostgreSQL, and built automated statistical Z-score anomaly detection pipelines in Python. Given your focus on {skills_str}, my track record in data infrastructure and decision support aligns directly with your team's goals.\n\n"
            f"I would welcome the opportunity to discuss how my analytical skills and fintech experience can contribute to {job['company']}.\n\n"
            f"Best regards,\nSagar Sohrab\nsagar7.sohrab@gmail.com | +91 8169052960"
        )

    report_md = generate_markdown_report(top_jobs)

    # Save to JOBS_DIGEST.md
    digest_path = os.path.join(os.path.dirname(__file__), "JOBS_DIGEST.md")
    with open(digest_path, "w", encoding="utf-8") as f:
        f.write(report_md)
    print(f"Report saved to {digest_path}")

    # Save to jobs_data.json for Web UI
    json_path = os.path.join(os.path.dirname(__file__), "jobs_data.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(top_jobs, f, indent=2)
    print(f"Structured JSON data saved to {json_path}")

    # Check for Email Dispatch
    email_user = os.environ.get("EMAIL_USERNAME")
    email_pass = os.environ.get("EMAIL_PASSWORD")
    recipient_email = os.environ.get("RECIPIENT_EMAIL", "sagar7.sohrab@gmail.com")

    if email_user and email_pass:
        print("Sending email digest...")
        send_email_digest(report_md, email_user, email_pass, recipient_email)
    else:
        print("EMAIL_USERNAME or EMAIL_PASSWORD not set. Skipping email dispatch.")

    # Output for GitHub Actions
    if "GITHUB_STEP_SUMMARY" in os.environ:
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(report_md)

if __name__ == "__main__":
    main()
