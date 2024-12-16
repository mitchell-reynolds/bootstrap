import pandas as pd
from pprint import pprint
from rapidfuzz import fuzz
from pymongo import MongoClient


# MongoDB connection details
mongo_uri = "mongodb://localhost:27017/"
clinical_trials_db = "clinical_trials_db"
clinical_trials_collection = "studies"
new_coll = "stocks_filter"

openfda_db = "openfda"
openfda_collection = "drugs"


def load_stock_data(file_path):
    return pd.read_csv(file_path)

def clean_clinical_trials_data(stock_data):
    company_list = list(stock_data['company_ct'].unique())
    print(f"Setting Up MongoDB instance to look up the", len(company_list), "unique companies in the stock dataset")
    client = MongoClient(mongo_uri)
    client[clinical_trials_db]["stocks_filter"].drop() # Only drops if true to ensure there aren't dupes, otherwise it'll continue
    clinical_trials = client[clinical_trials_db][clinical_trials_collection]
    stocks_filter_collection = client[clinical_trials_db][new_coll]

    clinical_trials_modules = {
        "protocolSection.identificationModule": 1,
        "protocolSection.sponsorCollaboratorsModule": 1,
        "protocolSection.designModule": 1,
        "protocolSection.oversightModule": 1,
        "protocolSection.statusModule": 1,
        "protocolSection.armsInterventionsModule": 1,
        "protocolSection.interventionBrowseModule": 1
    }

    query = {"protocolSection.sponsorCollaboratorsModule.leadSponsor.name": {"$in" : company_list}}
    results = list(clinical_trials.find(query, clinical_trials_modules))
    print("Inserting each doc into `clinical_trials_db` called `", new_coll, "`")
    for doc in results:
        stocks_filter_collection.insert_one(doc)

    # Close the connection to the "studies" collection
    client.close()

if __name__ == "__main__":
    stock_data = load_stock_data("./data_ingest/raw_data/merged_stock_data.csv")
    clinical_trials_data = clean_clinical_trials_data(stock_data)
