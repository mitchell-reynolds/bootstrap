import re
import csv
from pymongo import MongoClient

# MongoDB connection details
mongo_uri = "mongodb://localhost:27017/"
clinical_trials_db = "clinical_trials_db"
openfda_db = "openfda"
filtered_coll = "stocks_filter"

# Build FDA map
client = MongoClient(mongo_uri)
ct_collection = client[clinical_trials_db][filtered_coll]
fda_collection = client[openfda_db][filtered_coll]

# Normalize function: lowercase, remove trademarks/copyright symbols, strip whitespace, and split combined names
def normalize_name(name: str) -> list:
    name = name.lower()
    name = re.sub(r'[\u00ae\u2122\u00a9]', '', name)  # Remove symbols: ® = ®, ™ = ™, © = ©
    name = name.strip()
    # Split names by " and " or "/"
    split_names = re.split(r'\s+and\s+|/', name)
    return [n.strip() for n in split_names if n.strip()]

# Dynamic field configuration (add new fields here as needed)
FIELD_CONFIG = {
    "ct_fields": {
        "ct_name": lambda doc: [intervention.get("name", "") for intervention in doc.get("protocolSection", {}).get("armsInterventionsModule", {}).get("interventions", [])],
        "ct_otherNames": lambda doc: [name for intervention in doc.get("protocolSection", {}).get("armsInterventionsModule", {}).get("interventions", []) for name in intervention.get("otherNames", [])],
        "ct_sponsor": lambda doc: doc.get("protocolSection", {}).get("sponsorCollaboratorsModule", {}).get("leadSponsor", {}).get("name", ""),
        "ct_id": lambda doc: doc.get("protocolSection", {}).get("identificationModule", {}).get("nctId", ""),
        "ct_phase": lambda doc: doc.get("protocolSection", {}).get("designModule", {}).get("phases", ""),
        "ct_date": lambda doc: doc.get("protocolSection", {}).get("statusModule", {}).get("studyFirstPostDateStruct", {}).get("date", "")
    },
    "fda_fields": {
        "fda_brand": lambda doc: [p.get("brand_name", "") for p in doc.get("products", [])],
        "fda_generic": lambda doc: doc.get("openfda", {}).get("generic_name", []),
        "fda_active": lambda doc: [ingredient.get("name", "") for p in doc.get("products", []) for ingredient in p.get("active_ingredients", [])],
        "fda_company": lambda doc: doc.get("company_ct", ""),
        "fda_id": lambda doc: doc.get("application_number", ""),
        "fda_date": lambda doc: next((sub.get("submission_status_date", "") for sub in doc.get("submissions", []) if sub.get("submission_type") == "ORIG"), "")
    }
}

# Function to find matches and write to CSV
def combine_fda_and_ct():
    # Create a dictionary for quick lookup of FDA documents by company
    fda_docs_by_company = {}
    for fda_doc in fda_collection.find():
        fda_company = FIELD_CONFIG['fda_fields']['fda_company'](fda_doc).lower()
        if fda_company not in fda_docs_by_company:
            fda_docs_by_company[fda_company] = []
        fda_docs_by_company[fda_company].append(fda_doc)

    with open('./data_cleaning/processed_data/combine_fda_and_ct.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['ct_id', 'fda_id', 'fda_company', 'matched_drug_names', 'ct_date', 'fda_date', 'ct_phase', 'fda_brand', 'fda_generic', 'fda_active', 'ct_name', 'ct_otherNames', 'normalized_fda_drug_names'])

        for ct_doc in ct_collection.find():
            ct_sponsor = FIELD_CONFIG['ct_fields']['ct_sponsor'](ct_doc).lower()
            if ct_sponsor in fda_docs_by_company:
                # Filter out interventions with type "DEVICE" or name "Placebo"
                ct_interventions = ct_doc.get("protocolSection", {}).get("armsInterventionsModule", {}).get("interventions", [])
                ct_drug_names = set()
                for intervention in ct_interventions:
                    if intervention.get("type", "").lower() == "drug" and intervention.get("name", "").lower() != "placebo":
                        ct_drug_names.add(intervention.get("name", ""))
                        ct_drug_names.update(intervention.get("otherNames", []))

                normalized_ct_drug_names = {n for name in ct_drug_names for n in normalize_name(name)}

                for fda_doc in fda_docs_by_company[ct_sponsor]:
                    fda_drug_names = set(FIELD_CONFIG['fda_fields']['fda_brand'](fda_doc) + \
                                         FIELD_CONFIG['fda_fields']['fda_generic'](fda_doc) + \
                                         FIELD_CONFIG['fda_fields']['fda_active'](fda_doc))
                    normalized_fda_drug_names = {n for name in fda_drug_names for n in normalize_name(name)}

                    # Find intersection
                    matched_drug_names = normalized_fda_drug_names.intersection(normalized_ct_drug_names)

                    if matched_drug_names:
                        writer.writerow([
                            FIELD_CONFIG['ct_fields']['ct_id'](ct_doc),
                            FIELD_CONFIG['fda_fields']['fda_id'](fda_doc),
                            FIELD_CONFIG['fda_fields']['fda_company'](fda_doc),
                            ', '.join(matched_drug_names),
                            FIELD_CONFIG['ct_fields']['ct_date'](ct_doc),
                            FIELD_CONFIG['fda_fields']['fda_date'](fda_doc),
                            FIELD_CONFIG['ct_fields']['ct_phase'](ct_doc),
                            FIELD_CONFIG['fda_fields']['fda_brand'](fda_doc),
                            FIELD_CONFIG['fda_fields']['fda_generic'](fda_doc),
                            FIELD_CONFIG['fda_fields']['fda_active'](fda_doc),
                            FIELD_CONFIG['ct_fields']['ct_name'](ct_doc),
                            FIELD_CONFIG['ct_fields']['ct_otherNames'](ct_doc),
                            ', '.join(normalized_fda_drug_names)
                        ])

# Execute the function
combine_fda_and_ct()