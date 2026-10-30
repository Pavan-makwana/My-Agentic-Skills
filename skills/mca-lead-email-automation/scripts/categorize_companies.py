"""
categorize_companies.py
-----------------------
Intelligent multi-industry classification engine for MCA registered companies.

Maps companies based on:
  1. 21-digit CIN structure (embedded 5-digit NIC code at positions 5 to 10)
  2. Principal Business Activity / NIC description
  3. Company Name keyword analysis

Outputs assigned category, tailored services, pitch bullets, and matching email template.
"""

import re
import pandas as pd

# ── INDUSTRY DEFINITIONS & MAPPINGS ──────────────────────────────────────────

CATEGORIES = {
    "fintech_finance": {
        "display_name": "Finance, FinTech & Investment",
        "template_file": "templates/categories/fintech_finance.html",
        "nic_prefixes": [
            "64", "65", "66",      # Financial and insurance activities
            "64191", "64192", "64920", "64990", "66120", "66190",
        ],
        "keywords": [
            "finance", "fintech", "capital", "wealth", "investment", "invest", "nbfc",
            "microfinance", "lending", "credit", "asset", "securities", "broker",
            "trading", "payment", "wallet", "mutual fund", "chit fund", "treasury",
            "crypto", "forex", "fund", "insure", "insurance", "leasing"
        ],
        "services": [
            "High-Trust Financial Brand Website",
            "Finance Management CRM & Lead Pipeline",
            "Financial Portals, Invoicing & Billing Dashboard",
            "Custom Software Solutions",
        ],
        "starter_pack_name": "Finance & Wealth Digital Starter Pack",
    },

    "consultancy_professional": {
        "display_name": "Consultancy & Professional Services",
        "template_file": "templates/categories/consultancy_services.html",
        "nic_prefixes": [
            "69", "70", "71", "73", "74", "78",
            "69100", "69201", "70200", "71100", "73100", "78100",
        ],
        "keywords": [
            "consult", "consulting", "consultancy", "advisory", "legal", "advocate",
            "chartered", "tax", "taxation", "audit", "management", "human resource",
            "recruitment", "staffing", "marketing", "branding", "pr agency", "architect",
            "design", "strategy", "compliance", "business solutions", "associates"
        ],
        "services": [
            "High-Converting Corporate Website & Professional Brand Identity",
            "Consultancy CRM & Retainer Invoicing",
            "Client Portal & Automated Calendar Booking",
            "Custom Software Solutions",
        ],
        "starter_pack_name": "Professional Practice & Firm Digital Pack",
    },

    "healthcare_pharma": {
        "display_name": "Healthcare, Pharma & Life Sciences",
        "template_file": "templates/categories/healthcare_pharma.html",
        "nic_prefixes": [
            "21", "86", "87", "88",
            "21001", "21002", "86100", "86201", "86905",
        ],
        "keywords": [
            "health", "healthcare", "pharma", "pharmaceutical", "clinic", "hospital",
            "med", "medical", "medic", "life science", "biotech", "diagnostics",
            "pathology", "lab", "dental", "ayurved", "homeo", "wellness", "care",
            "therapeutics", "drugs", "doctor", "nursing", "rehab"
        ],
        "services": [
            "Official Healthcare & Clinic Website",
            "Clinic Management CRM & Patient Scheduling",
            "Pharmacy Billing & Inventory Management",
            "Custom Software Solutions",
        ],
        "starter_pack_name": "Healthcare Digital Suite & Clinic ERP",
    },

    "real_estate_construction": {
        "display_name": "Real Estate, Construction & Infrastructure",
        "template_file": "templates/categories/real_estate_construction.html",
        "nic_prefixes": [
            "41", "42", "43", "68",
            "41001", "41002", "42101", "43210", "68100", "68200",
        ],
        "keywords": [
            "build", "builder", "construction", "realty", "real estate", "property",
            "properties", "developer", "infra", "infrastructure", "homes", "housing",
            "estate", "acres", "concrete", "project", "civil", "architectural",
            "interior", "decor", "township", "promoters"
        ],
        "services": [
            "Modern Project Showcase Website",
            "Real Estate Lead CRM with Auto-Distribution",
            "Customer Booking & Payment Milestone Manager",
            "Custom Software Solutions",
        ],
        "starter_pack_name": "Real Estate Builder & Project Launch Pack",
    },

    "ecommerce_retail": {
        "display_name": "E-Commerce, D2C & Retail",
        "template_file": "templates/categories/ecommerce_retail.html",
        "nic_prefixes": [
            "47", "47912", "47911", "47110", "47190",
        ],
        "keywords": [
            "e-commerce", "ecommerce", "retail", "mart", "store", "shop", "online",
            "fashion", "apparel", "garment", "clothing", "wear", "jewel", "jewellery",
            "cosmetic", "beauty", "electronics", "gadget", "traders", "trading",
            "wholesale", "supermarket", "hypermarket", "d2c", "direct to consumer"
        ],
        "services": [
            "High-Conversion Custom E-Commerce Website",
            "Retail CRM, Inventory Sync & Order Management",
            "Shipping Automation & Payment Gateways",
            "Custom Software Solutions",
        ],
        "starter_pack_name": "All-in-One E-Commerce Launch Suite",
    },

    "education_edtech": {
        "display_name": "Education, EdTech & Training",
        "template_file": "templates/categories/education_edtech.html",
        "nic_prefixes": [
            "85", "85101", "85211", "85301", "85499",
        ],
        "keywords": [
            "education", "edtech", "academy", "institute", "school", "college",
            "university", "classes", "coaching", "learning", "training", "tuition",
            "tutorial", "vidya", "shiksha", "gurukul", "skills", "upskill",
            "test prep", "examination"
        ],
        "services": [
            "Official Institutional Brand Website",
            "Education CRM & Online Admission Portal",
            "Online Fee Collection & Digital Receipts",
            "Custom Software Solutions",
        ],
        "starter_pack_name": "EdTech & Institutional Management Suite",
    },

    "manufacturing_logistics": {
        "display_name": "Manufacturing, Industrial & Supply Chain",
        "template_file": "templates/categories/manufacturing_logistics.html",
        "nic_prefixes": [
            "13", "14", "15", "16", "17", "18", "19", "20", "22", "23", "24",
            "25", "26", "27", "28", "29", "30", "31", "32", "33",
            "49", "50", "51", "52", "53",
            "49231", "52101", "52291", "28110",
        ],
        "keywords": [
            "manufactur", "industr", "factory", "steel", "metal", "plastic", "chemical",
            "polymer", "engineering", "packaging", "pipes", "textile", "fabrics",
            "logistics", "supply chain", "freight", "cargo", "transport", "transportation",
            "warehouse", "warehousing", "shipping", "fleet", "courier", "export", "import"
        ],
        "services": [
            "Modern Industrial & Corporate Website",
            "Manufacturing & Operations Management CRM",
            "Warehouse & Inventory Tracking Portal",
            "Custom Software Solutions",
        ],
        "starter_pack_name": "Industrial Digital & Supply Chain Pack",
    },

    "food_beverage": {
        "display_name": "Food, Beverage & Hospitality",
        "template_file": "templates/categories/food_beverage.html",
        "nic_prefixes": [
            "10", "11", "56",
            "56101", "56210", "56290", "56301", "10101", "10711", "11001",
        ],
        "keywords": [
            "food", "foods", "beverage", "beverages", "restaurant", "cafe", "kitchen",
            "hospitality", "catering", "bakers", "bakery", "dairy", "sweets", "snacks",
            "agro", "cloud kitchen", "qsr", "dining", "eatery", "bistro", "dhaba",
            "tiffin", "canteen", "lounge", "grill", "spice", "masala", "mithai"
        ],
        "services": [
            "Custom Online Food Ordering Website",
            "FSSAI Food License & Compliance",
            "Smart POS Billing System (KOT & GST)",
            "Custom Software Solutions",
        ],
        "starter_pack_name": "All-in-One Food Business Starter Pack",
    },

    "it_software_saas": {
        "display_name": "IT, Software & SaaS",
        "template_file": "templates/categories/it_saas_tech.html",
        "nic_prefixes": [
            "58", "62", "63",
            "62011", "62012", "62020", "62090", "63110",
        ],
        "keywords": [
            "tech", "technology", "technologies", "software", "infotech", "it solutions",
            "digital", "systems", "cyber", "cloud", "ai", "artificial intelligence",
            "robotics", "automation", "data", "analytics", "saas", "app", "labs",
            "computing", "networks", "telecom"
        ],
        "services": [
            "Modern Tech Brand Website & Product Landing Pages",
            "Tech Talent Staffing & Dedicated Engineering",
            "Cloud Architecture & CI/CD DevOps Setup",
            "Custom Software Solutions",
        ],
        "starter_pack_name": "Tech Acceleration & Custom Engineering Suite",
    },
}

# General Corporate Fallback
FALLBACK_CATEGORY = {
    "key": "general_corporate",
    "display_name": "Corporate & Business Services",
    "template_file": "templates/categories/general_corporate.html",
    "services": [
        "Modern Corporate Website & Corporate Identity",
        "Custom Business Automation ERP & Billing Portal",
        "Google Workspace / Microsoft 365 Setup & Secure Cloud Migration",
        "CRM & Automated Customer Lead Capture",
    ],
    "starter_pack_name": "Enterprise Digital Launch Package",
}


def extract_nic_from_cin(cin: str) -> str:
    """
    In India, the 21-digit CIN has the format:
    U / L + 5-digit NIC Code + State (2 letters) + Year (4 digits) + PLC/PTC/LLP + 6-digit reg number
    Example: U56101DL2026PTC123456 -> NIC is 56101
    """
    cin = str(cin).strip().upper()
    m = re.match(r"^[UL]([0-9]{5})", cin)
    if m:
        return m.group(1)
    # Fallback to any 5 consecutive digits near start
    m2 = re.search(r"^[UL]?[A-Z]*([0-9]{4,5})", cin)
    if m2:
        return m2.group(1)
    return ""


def classify_company(row: pd.Series) -> dict:
    """
    Classifies a company into the best-matching industry category
    using CIN NIC code, Activity description, and Company Name.
    """
    cin = str(row.get("cin", "")).strip().upper()
    name = str(row.get("company_name", "")).strip()
    name_lower = name.lower()
    activity = str(row.get("activity", "")).lower()

    nic_code = extract_nic_from_cin(cin)

    # 1. Match by NIC Code Prefix (High Confidence)
    if nic_code:
        for cat_key, cat_data in CATEGORIES.items():
            for prefix in cat_data["nic_prefixes"]:
                if nic_code.startswith(prefix):
                    return {
                        "category_key": cat_key,
                        "display_name": cat_data["display_name"],
                        "nic_matched": nic_code,
                        "match_type": "NIC Code",
                        "template_file": cat_data["template_file"],
                        "starter_pack": cat_data["starter_pack_name"],
                        "services": cat_data["services"],
                    }

    # 2. Match by Company Name Keywords
    for cat_key, cat_data in CATEGORIES.items():
        for kw in cat_data["keywords"]:
            # Word boundary check to prevent substring false-positives
            if re.search(r"\b" + re.escape(kw) + r"\b", name_lower):
                return {
                    "category_key": cat_key,
                    "display_name": cat_data["display_name"],
                    "nic_matched": nic_code or "N/A",
                    "match_type": f"Name Keyword ({kw})",
                    "template_file": cat_data["template_file"],
                    "starter_pack": cat_data["starter_pack_name"],
                    "services": cat_data["services"],
                }

    # 3. Match by Activity Column Keywords
    if activity:
        for cat_key, cat_data in CATEGORIES.items():
            for kw in cat_data["keywords"]:
                if kw in activity:
                    return {
                        "category_key": cat_key,
                        "display_name": cat_data["display_name"],
                        "nic_matched": nic_code or "N/A",
                        "match_type": f"Activity Description ({kw})",
                        "template_file": cat_data["template_file"],
                        "starter_pack": cat_data["starter_pack_name"],
                        "services": cat_data["services"],
                    }

    # 4. Fallback to General Corporate
    return {
        "category_key": FALLBACK_CATEGORY["key"],
        "display_name": FALLBACK_CATEGORY["display_name"],
        "nic_matched": nic_code or "Unknown",
        "match_type": "Corporate Default",
        "template_file": FALLBACK_CATEGORY["template_file"],
        "starter_pack": FALLBACK_CATEGORY["starter_pack_name"],
        "services": FALLBACK_CATEGORY["services"],
    }


def categorize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Applies classification to an entire DataFrame of companies."""
    results = df.apply(classify_company, axis=1)
    res_df = pd.DataFrame(results.tolist())
    # Flatten services list into bullet strings for easy template injection
    res_df["services_formatted"] = res_df["services"].apply(
        lambda s_list: "\n".join(f"• {s}" for s in s_list)
    )
    return pd.concat([df.reset_index(drop=True), res_df.reset_index(drop=True)], axis=1)
