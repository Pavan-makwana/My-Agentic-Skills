"""
send_category_emails.py
-----------------------
Dynamic multi-industry outreach sender for ALOXO IT LLP.

Automatically selects the tailored HTML template based on each company's
nature of business (Fintech, Consultancy, Healthcare, Real Estate, E-Commerce,
Education, Manufacturing, Food & Beverage, IT/SaaS, Corporate).

Usage:
    # Preview pitches for all categories:
    python scripts/send_category_emails.py --dry-run

    # Send a sample of all category templates to an internal test email:
    python scripts/send_category_emails.py --test-email pavan561981@gmail.com

    # Run the live categorized outreach:
    python scripts/send_category_emails.py [path_to_categorized_xlsx]
"""

import os
import sys
import time
import random
import pathlib
import datetime
import smtplib
from string import Template
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
from dotenv import load_dotenv

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

load_dotenv()

LEADS_ROOT         = pathlib.Path("mca_leads")
PROCESSED_CINS_CSV = LEADS_ROOT / "processed_cins.csv"
OUTREACH_DELAY_MIN = 10
OUTREACH_DELAY_MAX = 20

SMTP_HOST           = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT           = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL        = os.getenv("SENDER_EMAIL", "").strip()
SENDER_APP_PASSWORD = os.getenv("SENDER_APP_PASSWORD", "").strip().replace(" ", "")
TEAM_INBOX_EMAIL    = os.getenv("TEAM_INBOX_EMAIL", "pavan561981@gmail.com")
AUTO_SEND_OUTREACH  = os.getenv("AUTO_SEND_OUTREACH", "false").strip().lower() == "true"
SENDER_NAME         = os.getenv("SENDER_NAME", "ALOXO IT Team")
SENDER_COMPANY      = os.getenv("SENDER_COMPANY", "ALOXO IT LLP")
SENDER_PHONE        = os.getenv("SENDER_PHONE", "+91 93137 33349")
SENDER_WEBSITE      = os.getenv("SENDER_WEBSITE", "https://quantatechlabs.com")


def get_smtp_connection() -> smtplib.SMTP:
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    server.ehlo()
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
    return server


def render_category_email(row: pd.Series) -> tuple[str, str]:
    """
    Renders the company's designated HTML category template with personalized details.
    Returns (subject, html_body).
    """
    template_path = pathlib.Path(str(row.get("template_file", "templates/categories/general_corporate.html")))
    if not template_path.exists():
        template_path = pathlib.Path("templates/categories/general_corporate.html")

    template_text = template_path.read_text(encoding="utf-8")
    t = Template(template_text)

    company_name = str(row.get("company_name", "Your Company")).strip()
    directors = str(row.get("directors", "")).split(",")[0].strip()
    director_name = directors if directors and directors.lower() not in ("nan", "") else "the Team"
    starter_pack = str(row.get("starter_pack", "Digital Acceleration Suite"))

    html_body = t.safe_substitute(
        company_name=company_name,
        director_or_team_name=director_name,
        sender_name=SENDER_NAME,
        sender_company=SENDER_COMPANY,
        sender_phone=SENDER_PHONE,
        sender_website=SENDER_WEBSITE,
    )

    subject = f"Congratulations on Incorporating {company_name}! {starter_pack}"
    return subject, html_body


def test_send_all_categories(target_email: str):
    """Sends one sample email for each industry category to an internal tester."""
    from process_historical_dataset import generate_sample_historical_data
    from categorize_companies import categorize_dataframe

    print(f"\n[test] Sending preview of each industry category template to {target_email} ...")
    raw_df = generate_sample_historical_data()
    classified_df = categorize_dataframe(raw_df)

    # Pick 1 sample company per category
    sample_categories = classified_df.drop_duplicates(subset=["category_key"]).copy()

    server = get_smtp_connection()
    count = 0

    for _, row in sample_categories.iterrows():
        subject, html = render_category_email(row)
        cat_name = row.get("display_name", "Industry")

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[{cat_name}] {subject}"
        msg["From"]    = SENDER_EMAIL
        msg["To"]      = target_email
        msg.attach(MIMEText(html, "html"))

        print(f"  ✉️ Sending category: {cat_name} -> {target_email} ...")
        server.sendmail(SENDER_EMAIL, target_email, msg.as_string())
        count += 1
        time.sleep(2)

    server.quit()
    print(f"\n🎉 Successfully delivered {count} category test emails to {target_email}!\n")


def main():
    if "--test-email" in sys.argv:
        idx = sys.argv.index("--test-email")
        if len(sys.argv) > idx + 1:
            test_send_all_categories(sys.argv[idx + 1])
        else:
            test_send_all_categories(TEAM_INBOX_EMAIL)
        return

    # Dry-run preview
    if "--dry-run" in sys.argv:
        from process_historical_dataset import generate_sample_historical_data
        from categorize_companies import categorize_dataframe
        raw_df = generate_sample_historical_data()
        classified_df = categorize_dataframe(raw_df)
        print("\n--- MULTI-INDUSTRY OUTREACH PREVIEW (DRY-RUN) ---")
        for _, row in classified_df.iterrows():
            subject, _ = render_category_email(row)
            print(f"[{row['display_name']}]")
            print(f"  Target: {row['company_name']} ({row.get('email', 'No email')})")
            print(f"  Subject: {subject}")
            print(f"  Starter Pack: {row['starter_pack']}")
            print(f"  Template: {row['template_file']}\n")
        return

    print("To test send previews, run: python scripts/send_category_emails.py --test-email <your_email>")


if __name__ == "__main__":
    main()
