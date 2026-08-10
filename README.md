# 🎯 Automated Job Finder Agent (GitHub Actions)

An autonomous job search agent that runs daily on GitHub Actions to scan open APIs and RSS feeds for **Business Analyst**, **Data Analyst**, **Product Analyst**, and **Analytics Engineer** roles tailored to **Sagar Sohrab**.

## 🚀 How It Works

1. **Daily Cloud Execution**: Triggered via GitHub Actions `cron` at 8:30 AM IST (03:00 UTC).
2. **Multi-Source Fetching**: Queries Remotive, Arbeitnow, Jobicy, and Google News RSS feeds.
3. **Relevance Scoring**: Evaluates job titles, locations (Bengaluru, Mumbai, Remote India), and key skill matches (`SQL`, `BigQuery`, `Python`, `Tableau`, `Power BI`, `Checkout Funnel`, `Z-score Anomaly Detection`).
4. **Digest Delivery**: Automatically updates `JOBS_DIGEST.md`, opens a GitHub Issue with the daily digest, and optionally dispatches Telegram / Email alerts.

## 🛠️ How to Deploy to Your GitHub Account

1. **Create a new GitHub Repository**:
   Create a new public or private repository on GitHub (e.g. named `job-finder-agent`).

2. **Initialize and Push**:
   ```bash
   cd C:\Users\Lenovo\.gemini\antigravity\scratch\job-finder-agent
   git init
   git add .
   git commit -m "feat: initial commit for automated job finder agent"
   git branch -M main
   git remote add origin https://github.com/YOUR_GITHUB_USERNAME/job-finder-agent.git
   git push -u origin main
   ```

3. **Enable GitHub Actions Permissions**:
   - Go to your repository settings on GitHub: **Settings** -> **Actions** -> **General**.
   - Under **Workflow permissions**, select **Read and write permissions**.
   - Click **Save**.

4. **(Optional) Configure Telegram Alerts**:
   - If you want daily messages on Telegram, add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` under **Settings** -> **Secrets and variables** -> **Actions**.

5. **Manual Trigger**:
   - Go to the **Actions** tab in your repository, select **Daily Job Finder Agent**, and click **Run workflow** to test it instantly!
