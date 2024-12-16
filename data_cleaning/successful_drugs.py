from pymongo import MongoClient
import json
import math

# MongoDB connection details
mongo_uri = "mongodb://localhost:27017/"
clinical_trials_db = "clinical_trials_db"
openfda_db = "openfda"
filtered_coll = "stocks_filter"

# Initialize MongoDB client
client = MongoClient(mongo_uri)

# Collections
ct_collection = client[clinical_trials_db][filtered_coll]
fda_collection = client[openfda_db][filtered_coll]

def fetch_sample_and_export():
    # Fetch document counts
    ct_count = ct_collection.count_documents({})
    fda_count = fda_collection.count_documents({})

    # Determine Sample Sizes
    ct_sample_size = max(1, math.ceil(ct_count * 0.001))
    fda_sample_size = max(1, math.ceil(fda_count * 0.1))

    # Fetch representative samples
    ct_sample = list(ct_collection.aggregate([{"$sample": {"size": ct_sample_size}}]))
    fda_sample = list(fda_collection.aggregate([{"$sample": {"size": fda_sample_size}}]))

    # Save to JSON files
    with open("./data_cleaning/processed_data/sample_ct.json", "w") as ct_file:
        json.dump(ct_sample, ct_file, default=str, indent=4)

    with open("./data_cleaning/processed_data/sample_fda.json", "w") as fda_file:
        json.dump(fda_sample, fda_file, default=str, indent=4)

def successful_drugs():

    return

