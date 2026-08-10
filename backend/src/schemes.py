"""
Hand-built dataset of major Indian government financial schemes.
Sources: official scheme portals (pmjdy.gov.in, jansuraksha.gov.in, mudra.org.in)
Last verified: July 2025
"""

from datetime import date

SCHEMES = [
    {
        "name": "PM Jan Dhan Yojana (PMJDY)",
        "description": "Zero-balance savings account with RuPay debit card and Rs 10,000 overdraft facility.",
        "eligibility": {
            "min_age": 10,
            "max_age": None,
            "requires_bank_account": False,
            "occupations": None,  # all
            "max_annual_income": None,  # all
        },
        "documents": ["Aadhaar card or any valid ID proof", "Address proof"],
        "apply_at": "Any bank branch or Business Correspondent",
    },
    {
        "name": "Pradhan Mantri Suraksha Bima Yojana (PMSBY)",
        "description": "Accidental death and disability insurance cover of Rs 2 lakh at just Rs 20 per year.",
        "eligibility": {
            "min_age": 18,
            "max_age": 70,
            "requires_bank_account": True,
            "occupations": None,
            "max_annual_income": None,
        },
        "documents": ["Bank account with auto-debit facility", "Aadhaar linked to bank account"],
        "apply_at": "Your bank branch or net banking portal",
    },
    {
        "name": "Pradhan Mantri Jeevan Jyoti Bima Yojana (PMJJBY)",
        "description": "Life insurance cover of Rs 2 lakh at Rs 436 per year for natural or accidental death.",
        "eligibility": {
            "min_age": 18,
            "max_age": 50,
            "requires_bank_account": True,
            "occupations": None,
            "max_annual_income": None,
        },
        "documents": ["Bank account with auto-debit facility", "Aadhaar linked to bank account"],
        "apply_at": "Your bank branch or net banking portal",
    },
    {
        "name": "Atal Pension Yojana (APY)",
        "description": "Guaranteed pension of Rs 1,000 to Rs 5,000 per month after age 60 for unorganised sector workers.",
        "eligibility": {
            "min_age": 18,
            "max_age": 40,
            "requires_bank_account": True,
            "occupations": ["unorganised", "self-employed", "daily wage", "farmer", "labour", "gig"],
            "max_annual_income": None,
            "not_income_taxpayer": True,
        },
        "documents": ["Bank account", "Aadhaar", "Mobile number linked to bank"],
        "apply_at": "Any bank branch or post office",
    },
    {
        "name": "PM Mudra Yojana (PMMY) — Shishu",
        "description": "Collateral-free business loan up to Rs 50,000 for micro enterprises.",
        "eligibility": {
            "min_age": 18,
            "max_age": None,
            "requires_bank_account": True,
            "occupations": ["self-employed", "small business", "shopkeeper", "vendor", "artisan"],
            "max_annual_income": None,
            "loan_amount_max": 50000,
        },
        "documents": ["ID proof", "Address proof", "Business proof or plan", "Bank statement (6 months)"],
        "apply_at": "Any bank, MFI, or NBFC",
    },
    {
        "name": "PM Mudra Yojana (PMMY) — Kishor",
        "description": "Collateral-free business loan from Rs 50,001 to Rs 5 lakh for growing micro enterprises.",
        "eligibility": {
            "min_age": 18,
            "max_age": None,
            "requires_bank_account": True,
            "occupations": ["self-employed", "small business", "shopkeeper", "vendor", "artisan"],
            "max_annual_income": None,
            "loan_amount_max": 500000,
        },
        "documents": ["ID proof", "Address proof", "Business proof", "Bank statement (6 months)", "ITR if available"],
        "apply_at": "Any bank, MFI, or NBFC",
    },
]


def check_eligibility(age: int, has_bank_account: bool, occupation: str, is_income_taxpayer: bool) -> dict:
    """
    Check which government schemes the caller is eligible for.
    Returns eligible schemes with documents needed and where to apply.
    Data source: hand-built from official scheme portals, last verified July 2025.
    """
    eligible = []
    ineligible = []
    occ_lower = occupation.lower()

    for scheme in SCHEMES:
        e = scheme["eligibility"]
        reasons = []

        if e["min_age"] and age < e["min_age"]:
            reasons.append(f"minimum age is {e['min_age']}")
        if e["max_age"] and age > e["max_age"]:
            reasons.append(f"maximum age is {e['max_age']}")
        if e["requires_bank_account"] and not has_bank_account:
            reasons.append("requires a bank account")
        if e.get("not_income_taxpayer") and is_income_taxpayer:
            reasons.append("not available for income taxpayers")
        if e["occupations"] and not any(o in occ_lower for o in e["occupations"]):
            reasons.append(f"meant for {', '.join(e['occupations'])}")

        if reasons:
            ineligible.append({"name": scheme["name"], "reasons": reasons})
        else:
            eligible.append({
                "name": scheme["name"],
                "description": scheme["description"],
                "documents": scheme["documents"],
                "apply_at": scheme["apply_at"],
            })

    return {
        "as_of": date.today().isoformat(),
        "data_source": "Hand-built from official scheme portals (pmjdy.gov.in, jansuraksha.gov.in, mudra.org.in). Last verified July 2025.",
        "eligible": eligible,
        "ineligible_count": len(ineligible),
    }
