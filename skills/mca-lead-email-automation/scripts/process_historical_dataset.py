"""
process_historical_dataset.py
-----------------------------
Processes historical MCA registration datasets (e.g. past 12 months).

Capabilities:
  1. Scans mca_leads/historical_12_months/raw/ (or any specified folder)
     for downloaded Excel / CSV / ZIP reports.
  2. Normalizes column headers across different month report formats.
  3. Deduplicates companies by CIN across all months.
  4. Classifies each company into its Industry Category using `categorize_companies.py`.
  5. Generates summary metrics (Total leads, Category breakdown, State distribution).
  6. Exports:
     - mca_leads/historical_12_months/all_companies_categorized.xlsx
     - Separate category workbooks (e.g. fintech_leads.xlsx, consultancy_leads.xlsx)
"""

import os
import sys
import glob
import pathlib
import datetime
import pandas as pd

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from categorize_companies import categorize_dataframe, CATEGORIES, FALLBACK_CATEGORY
from filter_food_companies import load_report, normalise_columns

HISTORICAL_DIR = pathlib.Path("mca_leads") / "historical_12_months"
RAW_DIR        = HISTORICAL_DIR / "raw"
OUTPUT_DIR     = HISTORICAL_DIR / "processed"


def generate_sample_historical_data() -> pd.DataFrame:
    """Generates a rich, realistic sample 12-month MCA dataset for testing."""
    sample_records = [
        # FinTech / Finance
        {"cin": "U64990DL2025PTC389101", "company_name": "KuberPay Digital Lending Solutions Pvt Ltd", "state": "Delhi", "directors": "Vikas Malhotra", "activity": "Other financial service activities", "email": "contact@kuberpay.sample"},
        {"cin": "U65999MH2025PTC392014", "company_name": "Zenith Wealth & Capital Advisors LLP", "state": "Maharashtra", "directors": "Sneha Deshmukh", "activity": "Financial intermediation auxiliary", "email": "advisory@zenithwealth.sample"},
        
        # Consultancy / Professional
        {"cin": "U69201KA2025PTC390451", "company_name": "Apex Global Tax & Strategy Consulting Pvt Ltd", "state": "Karnataka", "directors": "Arjun Rao", "activity": "Accounting, bookkeeping and auditing activities; tax consultancy", "email": "info@apexconsulting.sample"},
        {"cin": "U70200TN2025PTC391122", "company_name": "Catalyst Corporate Advisory & Law Associates LLP", "state": "Tamil Nadu", "directors": "K. Sundaram", "activity": "Management consultancy activities", "email": "legal@catalystassociates.sample"},

        # Healthcare / Pharma
        {"cin": "U86100TG2025PTC393301", "company_name": "AuraCare Multispeciality Clinics & Diagnostic Pvt Ltd", "state": "Telangana", "directors": "Dr. R. K. Varma", "activity": "Hospital activities", "email": "care@auracare.sample"},
        {"cin": "U21001GJ2025PTC394412", "company_name": "BioSynthetica Pharmaceuticals Pvt Ltd", "state": "Gujarat", "directors": "Bhavesh Patel", "activity": "Manufacture of pharmaceuticals, medicinal chemical", "email": "sales@biosynthetica.sample"},

        # Real Estate / Construction
        {"cin": "U41001HR2025PTC395521", "company_name": "Skyline Heights Infrastructure & Builders Pvt Ltd", "state": "Haryana", "directors": "Amitabh Choudhary", "activity": "Construction of buildings", "email": "projects@skylineheights.sample"},
        {"cin": "U68100UP2025PTC396632", "company_name": "GreenTerra Realty & Township Developers LLP", "state": "Uttar Pradesh", "directors": "Sunil Yadav", "activity": "Real estate activities with own or leased property", "email": "invest@greenterra.sample"},

        # E-Commerce & Retail
        {"cin": "U47912WB2025PTC397743", "company_name": "VelvetLoom D2C Fashion & Apparel Pvt Ltd", "state": "West Bengal", "directors": "Ananya Ghosh", "activity": "Retail sale via mail order houses or via Internet", "email": "hello@velvetloom.sample"},
        {"cin": "U47190RJ2025PTC398854", "company_name": "Heritage Crafts & Organic Living Store Pvt Ltd", "state": "Rajasthan", "directors": "Mahipal Singh", "activity": "Other non-specialized retail sale", "email": "store@heritagecrafts.sample"},

        # Education & EdTech
        {"cin": "U85499DL2025PTC399965", "company_name": "EduNova NextGen Learning & Skill Academy Pvt Ltd", "state": "Delhi", "directors": "Pooja Batra", "activity": "Other education n.e.c.", "email": "admissions@edunova.sample"},

        # Manufacturing & Industrial
        {"cin": "U28110MH2025PTC401076", "company_name": "Dynamix Heavy Forgings & Precision Engineering Pvt Ltd", "state": "Maharashtra", "directors": "Nitin Kulkarni", "activity": "Manufacture of structural metal products", "email": "works@dynamixengg.sample"},

        # IT & Tech / SaaS
        {"cin": "U62011KA2025PTC402187", "company_name": "CognitiveMatrix AI Cloud Technologies Pvt Ltd", "state": "Karnataka", "directors": "Kiran Nambiar", "activity": "Computer programming, consultancy and related activities", "email": "tech@cognitivematrix.sample"},

        # Food & Beverage
        {"cin": "U56101DL2025PTC403298", "company_name": "Biryani Express Cloud Kitchens & Hospitality Pvt Ltd", "state": "Delhi", "directors": "Farhan Qureshi", "activity": "Restaurants and mobile food service activities", "email": "orders@biryaniexpress.sample"},
    ]
    return pd.DataFrame(sample_records)


def process_folder(input_dir: pathlib.Path = RAW_DIR) -> pd.DataFrame:
    """Loads all report files from the input folder or falls back to sample dataset."""
    files = list(input_dir.glob("**/*.*"))
    valid_files = [f for f in files if f.suffix.lower() in (".xlsx", ".xls", ".csv", ".zip")]

    if valid_files:
        print(f"[history] Found {len(valid_files)} historical raw files in {input_dir}")
        dfs = []
        for f in valid_files:
            try:
                df = load_report(f)
                df = normalise_columns(df)
                dfs.append(df)
            except Exception as e:
                print(f"  [warn] Could not load {f.name}: {e}")
        combined = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
    else:
        print(f"[history] No files placed in {input_dir} yet. Using representative 12-month sample dataset...")
        combined = generate_sample_historical_data()

    if combined.empty:
        print("[history] No data available.")
        return pd.DataFrame()

    # Deduplicate by CIN
    if "cin" in combined.columns:
        before = len(combined)
        combined = combined.drop_duplicates(subset=["cin"])
        print(f"[history] Total records: {len(combined):,} (Deduplicated from {before:,})")

    # Run Multi-Industry Classification
    print("[history] Classifying companies across all industry categories...")
    classified_df = categorize_dataframe(combined)

    # Save consolidated dataset
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    today_str = datetime.date.today().strftime("%Y-%m")
    out_master = OUTPUT_DIR / f"all_companies_categorized_{today_str}.xlsx"

    with pd.ExcelWriter(out_master, engine="openpyxl") as writer:
        classified_df.to_excel(writer, sheet_name="All Companies", index=False)
        
        # Summary Sheet
        summary = classified_df["display_name"].value_counts().reset_index()
        summary.columns = ["Industry Category", "Company Count"]
        summary.to_excel(writer, sheet_name="Industry Breakdown", index=False)

    print(f"[history] ✅ Saved master categorized dataset to {out_master}")

    # Generate individual category files
    for cat_key, cat_group in classified_df.groupby("category_key"):
        cat_file = OUTPUT_DIR / f"{cat_key}_leads_{today_str}.xlsx"
        cat_group.to_excel(cat_file, index=False)

    print(f"[history] ✅ Generated individual category files in {OUTPUT_DIR}")
    return classified_df


def print_summary(df: pd.DataFrame):
    if df.empty:
        return
    print("\n" + "=" * 80)
    print("HISTORICAL DATASET: INDUSTRY CATEGORY BREAKDOWN")
    print("=" * 80)
    counts = df["display_name"].value_counts()
    for cat_name, count in counts.items():
        pct = (count / len(df)) * 100
        print(f"  • {cat_name:<45} : {count:>4} leads ({pct:>5.1f}%)")
    print("-" * 80)
    print(f"  Total Categorized Companies: {len(df):,}")
    print("=" * 80 + "\n")


def main():
    df = process_folder()
    print_summary(df)


if __name__ == "__main__":
    main()
