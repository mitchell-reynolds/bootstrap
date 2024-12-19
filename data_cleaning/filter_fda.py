import pandas as pd
from pprint import pprint
from rapidfuzz import fuzz
from pymongo import MongoClient
import re

# MongoDB connection details
mongo_uri = "mongodb://localhost:27017/"
clinical_trials_db = "clinical_trials_db"
openfda_db = "openfda"
openfda_collection = "drugs"
new_coll = "stocks_filter"

def load_stock_data(file_path):
    return pd.read_csv(file_path)

def preprocess_text(text):
    # Remove punctuation, make lowercase, and remove specific words
    text = re.sub(r'[\.,]', '', text).lower()
    text = re.sub(r'\b(pharmaceutical|biomedical|pharm|lifesciences|technology|diagnostics|ltd|holdings|corp|corporation|therapies|health|medicines|labs|laboratories|limited|technologies|inc|llc|therapeutics|pharmaceuticals|biotherapeutics|biosciences|pharma|plc|biotechnology|therapeutix|sciences|life sciences|medical)\b', '', text)
    return re.sub(r'\s+', ' ', text).strip()

def filter_fda(threshold):
    """
    Fetch unique sponsor names from fda_coll, match them with stock_data["company_ct"] using rapidfuzz,
    and store the lookup table into a CSV file with a similarity threshold.
    """
    client = MongoClient(mongo_uri)
    fda_coll = client[openfda_db][openfda_collection]
    
    # Drop coll if exists, then create coll for filtered FDA data based on stocks
    client[openfda_db][new_coll].drop()
    filtered_fda = client[openfda_db][new_coll]

    # Fetch unique sponsor names from FDA collection
    sponsor_names = fda_coll.distinct("sponsor_name")

    # Preprocess sponsor names
    processed_sponsors = {sponsor: preprocess_text(sponsor) for sponsor in sponsor_names}

    # Load stock data
    stock_data = load_stock_data("./data_ingest/raw_data/merged_stock_data.csv")
    company_ct_list = stock_data["company_ct"].dropna().unique()

    # Match sponsor names with company_ct using rapidfuzz
    matches = []
    for sponsor, processed_sponsor in processed_sponsors.items():
        best_match, best_score = None, 0
        for company_ct in company_ct_list:
            processed_company = preprocess_text(company_ct)
            score = fuzz.ratio(processed_sponsor, processed_company)
            if score > best_score and score >= threshold:
                best_match, best_score = company_ct, score
        if best_match:
            matches.append({"company_fda": sponsor, "company_ct": best_match})

    # Create a DataFrame for the lookup table
    lookup_df = pd.DataFrame(matches)
    lookup_df.to_csv("./data_cleaning/processed_data/ct_fda_lkup.csv", index=False, columns=["company_fda", "company_ct"])

    # FDA
    fda_company_list = list(lookup_df.company_fda.unique())
    fda_modules = {
        "application_number": 1,
        "sponsor_name": 1,
        "products": 1,
        "openfda.generic_name": 1,
        "submissions": {"$elemMatch": {"submission_type": "ORIG"}}
    }

    query = {"sponsor_name": {"$in" : fda_company_list}}
    results = list(fda_coll.find(query, fda_modules))
    # Map company_fda to company_ct for quick lookup
    company_ct_map = dict(zip(lookup_df.company_fda, lookup_df.company_ct))

    for doc in results:
        sponsor_name = doc.get("sponsor_name")
        doc["company_ct"] = company_ct_map[sponsor_name]  # Add company_ct to the document
        filtered_fda.insert_one(doc)


if __name__ == "__main__":
    filter_fda(95)
