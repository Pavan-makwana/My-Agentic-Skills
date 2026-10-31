# Autonomous MCA Multi-Industry Email Automation Guide

> A plug-and-play B2B lead generation and personalized cold outreach system. Automatically scrapes newly incorporated companies from the **Ministry of Corporate Affairs (MCA)**, classifies them by their **nature of business** (via 5-digit NIC codes), checks whether they have a live website, and sends tailored, **zero-emoji** outreach emails from your official domain or Gmail account.

[![GitHub Repo](https://img.shields.io/badge/GitHub-My--Agentic--Skills-blue?style=for-the-badge&logo=github)](https://github.com/Pavan-makwana/My-Agentic-Skills)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-brightgreen?style=for-the-badge&logo=python)](https://python.org)
[![Antigravity Compatible](https://img.shields.io/badge/Antigravity-Compatible-8c1226?style=for-the-badge&logo=google)](https://github.com/Pavan-makwana/My-Agentic-Skills)

---

## 3-Minute Setup on Your PC

### Step 1: Clone the Repository
Open your terminal (PowerShell on Windows, or Terminal on macOS/Linux) and run:

```bash
git clone https://github.com/Pavan-makwana/My-Agentic-Skills.git
cd My-Agentic-Skills/skills/mca-lead-email-automation
```

---

### Step 2: Install Python Packages
Make sure you have Python 3.10+ installed. Then install the required libraries:

```bash
pip install requests beautifulsoup4 pandas openpyxl python-dotenv
```

---

### Step 3: Configure Your Sender Details (`.env`)
Create a file named `.env` inside `mca-lead-email-automation/` and paste the following:

```ini
# SMTP / Email Settings (Gmail)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your_email@gmail.com
SENDER_APP_PASSWORD=xxxx xxxx xxxx xxxx

# Where internal reports and lead spreadsheets will be sent
TEAM_INBOX_EMAIL=your_email@gmail.com

# Safety switch:
# Set to 'false' for dry-run / draft mode (safe, sends no emails to real companies)
# Set to 'true' only when you are ready to auto-send outreach to verified leads
AUTO_SEND_OUTREACH=false

# Your Business Branding (appears in all email footers)
SENDER_NAME=Your Name / Team
SENDER_COMPANY=Your Company Name
SENDER_PHONE=+91 98765 43210
SENDER_WEBSITE=https://yourwebsite.com
```

#### How to Get Your 16-Character Google App Password:
1. Go to [myaccount.google.com/security](https://myaccount.google.com/security) and ensure **2-Step Verification** is turned **ON**.
2. Open [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).
3. Type `Antigravity` in the app name box and click **Create**.
4. Copy the 16-character password (e.g. `abcd efgh ijkl mnop`) and paste it into `SENDER_APP_PASSWORD` in your `.env`.

---

## Instant Testing Commands

### 1. Dry-Run Preview (Sends 0 emails, safe test)
Check how sample companies are categorized and preview which email template each business gets:
```bash
python scripts/send_category_emails.py --dry-run
```

### 2. Send All 10 Industry Categories to Your Email
Sends a sample email for every single industry directly to your inbox so you can review the layout and copy:
```bash
python scripts/send_category_emails.py --test-email your_email@gmail.com
```

### 3. Ingest and Categorize Historical Datasets
Drop any monthly MCA Excel or CSV file into `mca_leads/historical_12_months/raw/` and run:
```bash
python scripts/process_historical_dataset.py
```
This automatically produces a master categorized workbook and separates companies into distinct industry files (`fintech_leads.xlsx`, `real_estate_leads.xlsx`, `healthcare_leads.xlsx`, etc.).

---

## Supported Industry Verticals

Every Indian company's 21-digit CIN embeds a 5-digit **NIC code** at positions 5 to 10 (e.g. `U64990...` = FinTech, `U86100...` = Healthcare). The system matches each company to its industry:

| # | Industry Category | NIC Division | Pitched Starter Pack | Key Offerings Included |
|---|---|---|---|---|
| **1** | **Finance, Wealth & FinTech** | Division 64–66 | Finance & Wealth Digital Pack | Financial Website, Finance CRM & Lead Pipeline, Invoicing Dashboard, Custom Software Solutions |
| **2** | **Consultancy & Legal Practice** | Division 69–74 | Professional Practice Pack | Corporate Web Presence, Consultancy CRM & Billing, Client Portal & Calendar Sync, Custom Software Solutions |
| **3** | **Healthcare, Clinics & Pharma** | Division 21, 86–88 | Healthcare Digital Suite | Clinic Website, Clinic CRM & Scheduling, Pharmacy Inventory & Billing, Custom Software Solutions |
| **4** | **Real Estate & Construction** | Division 41–43, 68 | Real Estate Builder Pack | 3D Project Showcase Website, Real Estate Lead CRM, Booking & Milestone Manager, Custom Software Solutions |
| **5** | **E-Commerce, D2C & Retail** | Division 47 | E-Commerce Launch Suite | Custom E-Commerce Website, Retail CRM & Stock Sync, Shipping API Integration, Custom Software Solutions |
| **6** | **Education, EdTech & Academies** | Division 85 | EdTech Management Suite | Institutional Brand Website, Education CRM & Admissions, Online Fee Collection, Custom Software Solutions |
| **7** | **Manufacturing & Logistics** | Division 13–33, 49–53 | Industrial Digital Pack | Industrial Corporate Website, Manufacturing CRM, Warehouse & Stock Portal, Custom Software Solutions |
| **8** | **IT, Software & SaaS Startups** | Division 58, 62, 63 | Tech Acceleration Suite | Tech Brand Website & Landing Pages, Dedicated Developer Staffing, Cloud DevOps Setup, Custom Software Solutions |
| **9** | **Food, Beverage & Hospitality** | Division 56, 10, 11 | Food Business Starter Pack | Direct Food Ordering Website, FSSAI Food Licensing, Smart POS Billing (KOT & GST), Custom Software Solutions |
| **10**| **General Corporate (Fallback)** | All Others | Enterprise Digital Launch | Corporate Website, Business Management CRM, Operations Automation, Custom Software Solutions |

---

## Key Features

1. **Strict Zero-Emoji Standard:** Every template is 100% clean of emojis to prevent spam filters from flagging your emails and to maintain a professional B2B corporate tone.
2. **Website Detection Engine:** Detects whether a company has a live website, no website, or is stuck on a **"Coming Soon"** countdown placeholder. Companies without websites are marked **`HIGH — No Website`** priority.
3. **Dual Email Output:**
   - **Internal Report:** Sends a compiled Excel spreadsheet to your team inbox with breakdown metrics.
   - **Personalized Outreach:** Sends an industry-tailored email pitching an official website, industry CRM, and custom software.
4. **Duplicate Prevention:** Records every emailed company CIN in `mca_leads/processed_cins.csv` so no company is ever emailed twice.

---

## Run with Google Antigravity (Autonomous Agent)

If you use Google Antigravity, you can install this skill globally so your AI agent runs it autonomously on schedule:

### Windows PowerShell:
```powershell
Copy-Item -Recurse -Force "My-Agentic-Skills\skills\mca-lead-email-automation" "$env:USERPROFILE\.gemini\config\skills\"
```

### macOS / Linux:
```bash
cp -r My-Agentic-Skills/skills/mca-lead-email-automation ~/.gemini/config/skills/
```

### Prompt Your Agent in Antigravity Chat:
> *"Run the `mca-lead-email-automation` skill, filter newly registered companies by industry, and send the test preview to my email."*

---

## Scheduled Monthly Cron Expression

To check the MCA portal automatically on the **5th, 10th, and 15th** of every month at **10:00 AM IST**:
```
CRON_TZ=Asia/Kolkata 0 10 5,10,15 * *
```
*(If no new monthly MCA file is detected on that date, the script logs the check and exits cleanly without sending duplicate emails).*
