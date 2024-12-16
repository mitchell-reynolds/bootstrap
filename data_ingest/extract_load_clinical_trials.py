import time
import pymongo
import requests


# Main variables
BASE_URL = "https://clinicaltrials.gov/api/v2/studies"
PAGE_SIZE = 1000  # Number of records allowed per page
MONGO_URI = "mongodb://localhost:27017/"  # Default MongoDB location on local
db_name = "clinical_trials_db"
collection_name = "studies"


def fetch_page(params):
    """
    Fetch a single page of results from the ClinicalTrials.gov API
    """

    response = requests.get(BASE_URL, params=params)
    print("Fetching data from:", BASE_URL + '?' + '&'.join([f"{k}={v}" for k, v in params.items()]))
    if response.status_code != 200:
        raise requests.exceptions.RequestException(f"Failed to fetch data: {response.status_code}")
    return response.json()


def main():
    """
    With your MongoDB instance up, query the API and load in each study
    """
    print(f"Setting up MongoDB instance")
    client = pymongo.MongoClient(MONGO_URI)
    db = client[db_name]
    db[collection_name].drop()
    collection = db[collection_name]

    params = {
        "pageSize": PAGE_SIZE
    }

    while True:
        try:
            data = fetch_page(params)
            studies = data.get("studies", [])

            if not studies:
                print("No more data returned from the API.")
                break

            # Insert fetched results into MongoDB
            for study in studies:
                collection.insert_one(study)

            # Check for nextPageToken and update the params or break the loop
            next_page_token = data.get("nextPageToken")
            if next_page_token:
                params["pageToken"] = next_page_token
            else:
                break  # Exit the loop if no nextPageToken is present

            # Add a small delay to avoid hitting rate limits, if the API has them.
            time.sleep(0.1)

        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            break

    print("Data download complete!")


if __name__ == "__main__":
    main()
