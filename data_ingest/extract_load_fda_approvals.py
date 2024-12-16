import os
import json
import requests
import zipfile
from pymongo import MongoClient

# Main variables
BASE_URL = "https://download.open.fda.gov/drug/drugsfda/drug-drugsfda-0001-of-0001.json.zip"
FILE_PATH = "./data_ingest/raw_data/"
MONGO_URI = "mongodb://localhost:27017/"  # Default MongoDB location on local
db_name = "openfda"
collection_name = "drugs"


def download_fda():
    """
    MVP for downloading all FDA approval data
    """

    # Ensure the directory exists
    os.makedirs(FILE_PATH, exist_ok=True)

    # Define the local file paths
    zip_file_path = os.path.join(FILE_PATH, "downloaded_file.zip")

    # Download the file
    response = requests.get(BASE_URL, stream=True)
    response.raise_for_status()

    with open(zip_file_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    # Unzip the file
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(FILE_PATH)

    # Optional: Remove the zip file after extraction
    os.remove(zip_file_path)

    # Load the extracted JSON data
    json_file_path = os.path.join(FILE_PATH, "drug-drugsfda-0001-of-0001.json")
    with open(json_file_path, "r") as json_file:
        data = json.load(json_file)

    return data["results"]


def chunk_data(data, chunk_size):
    """
    Splits data into chunks of a specified size.
    """
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]


def main():
    """
    With your MongoDB instance up, upload the FDA data into your database
    """

    # Download the FDA data
    print(f"Downloading FDA Data")
    fda_data = download_fda()

    # Connect to MongoDB
    print(f"Spinning up MongoDB instance")
    client = MongoClient(MONGO_URI)
    db = client[db_name]
    collection = db[collection_name]

    # Handle large documents by splitting them
    print(f"Inserting FDA data into MongoDB")
    if isinstance(fda_data, list):
        for chunk in chunk_data(fda_data, 1000):  # Adjust chunk size as needed
            try:
                collection.insert_many(chunk)
            except Exception as e:
                print(f"Error inserting chunk: {e}")
    else:
        try:
            collection.insert_one(fda_data)
        except Exception as e:
            print(f"Error inserting document: {e}")

    print(f"Data successfully loaded into MongoDB database '{db_name}', collection '{collection_name}'.")


if __name__ == "__main__":
    main()
