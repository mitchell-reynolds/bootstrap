import requests
import json
import time
import os

# Example variables - adjust these to your specific API and needs
BASE_URL = "https://clinicaltrials.gov/api/v2/studies"
PAGE_SIZE = 1000  # Number of records per page (adjust based on API limits)
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "raw_data/clinical_trials_raw.json")


def fetch_page(params):
    """
    Fetch a single page of results from the API.
    Adjust accordingly if the API uses a different pattern.
    """
    response = requests.get(BASE_URL, params=params)
    print("Fetching data from:", BASE_URL + '?' + '&'.join([f"{k}={v}" for k, v in params.items()]))
    if response.status_code != 200:
        raise requests.exceptions.RequestException(f"Failed to fetch data: {response.status_code}")
    return response.json()


def main():
    params = {
        "pageSize": PAGE_SIZE
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("[")  # Start JSON array
        first_entry = True

        while True:
            try:
                data = fetch_page(params)
                studies = data.get("studies", [])

                if not studies:
                    print("No more data returned from the API.")
                    break

                # Write fetched results to disk incrementally
                for study in studies:
                    if not first_entry:
                        f.write(",")
                    json.dump(study, f, ensure_ascii=False)
                    first_entry = False

                # Check for nextPageToken and update the params or break the loop
                next_page_token = data.get("nextPageToken")
                if next_page_token:
                    params["pageToken"] = next_page_token
                else:
                    break  # Exit the loop if no nextPageToken is present

                # Add a small delay to avoid hitting rate limits, if the API has them.
                time.sleep(0.5)

            except requests.exceptions.RequestException as e:
                print(f"An error occurred: {e}")
                break

        f.write("]")  # End JSON array

    print("Data download complete.")


if __name__ == "__main__":
    main()
