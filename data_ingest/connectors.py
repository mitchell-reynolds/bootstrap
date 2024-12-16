import os
import json
import requests
import pandas as pd
import requests_cache
import yfinance as yf 
from munch import Munch
from dotenv import load_dotenv
from yahoofinancials import YahooFinancials
from ratelimit import limits, sleep_and_retry

# Load environment variables from .env file
load_dotenv()
openFDA_api_key = os.getenv("OPENFDA_API_KEY")

# cache API calls in a sqllite file to reduce the number of requests to openfda server
requests_cache.install_cache('openfda_cache')

OPENFDA_API = "https://api.fda.gov/drug/event.json"
OPENFDA_METADATA_YAML = "https://open.fda.gov/fields/drugevent.yaml"

@sleep_and_retry
@limits(calls=40, period=60)

def call_api(params):
    """
    OpenFDA API call. Respects rate limit. Overrides default data limit
    Input: dictionary with API parameters {search: '...', count: '...'}
    Output: nested dictionary representation of the JSON results section
    
    OpenFDA API rate limits:
         With no API key: 40 requests per minute, per IP address. 1000 requests per day, per IP address.
         With an API key: 240 requests per minute, per key. 120000 requests per day, per key.
    """
    if not params:
        params = {}
    params['limit'] = params.get('limit', 1000)

    # Uncomment the next line to add API key from .env
    # params['api_key'] = openFDA_api_key

    response = requests.get(OPENFDA_API, params=params)
    # print(response.url)

    if response.status_code != 200:
        raise Exception('API response: {}'.format(response.status_code))
    return response.json()['results']

def api_meta():
    """
    YAML file with field description and other metadata retrieved from the OpenFDA website
    Parses YAML file and provides syntactic sugar for accessing nested dictionaries
    Example: .patient.properties.patientagegroup.possible_values.value
    Note: reserved words, such as count and items still have to be accessed via ['count'], ['items']
    """

    response = requests.get(OPENFDA_METADATA_YAML)
    if response.status_code != 200:
        raise Exception('Could not retrieve YAML file with drug event API fields')
    
    # munch is a yaml parser with javascript-style object access
    y = Munch.fromYAML(response.text)
    return y['properties']

# Print api_meta in pretty JSON format
print(json.dumps(api_meta(), indent=4))


pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

def clinical_trials():
    # Initial URL for the first API call
    base_url = "https://clinicaltrials.gov/api/v2/studies"
    params = {
        "pageSize": 1000
    }

    # Initialize an empty list to store the data
    data_list = []
    count = 0

    # Loop until there is no nextPageToken
    while True:
        # Print the current URL (for debugging purposes)
        print("Fetching data from:", base_url + '?' + '&'.join([f"{k}={v}" for k, v in params.items()]))
        
        # Send a GET request to the API
        response = requests.get(base_url, params=params)

        # Check if the request was successful
        if response.status_code == 200:
            count += 1
            data = response.json()  # Parse JSON response
            studies = data.get('studies', [])  # Extract the list of studies

            # Loop through each study and extract specific information
            for study in studies:
                # Safely access nested keys
                nct_id = study['protocolSection']['identificationModule'].get('nctId', 'Unknown')
                brief_title = study['protocolSection']['identificationModule'].get('briefTitle', 'Unknown')
                sponsor_name = study['protocolSection']['sponsorCollaboratorsModule'].get('leadSponsor', {}).get('name', 'Unknown')
                sponsor_class = study['protocolSection']['sponsorCollaboratorsModule'].get('leadSponsor', {}).get('class', 'Unknown')
                has_results = study.get('hasResults', 'Unknown')
                overall_status = study['protocolSection']['statusModule'].get('overallStatus', 'Unknown')
                try:
                    phases = study['protocolSection']['designModule'].get('phases', 'Unknown')
                except:
                    phases = 'Unknown'
                # brief_summary = study['protocolSection']['descriptionModule'].get('briefSummary', 'Unknown')
                # startDate = study['protocolSection']['statusModule'].get('startDateStruct', {}).get('date', 'Unknown Date')
                # TODO: protocolSection.interventions.name; oversightModule.isFdaRegulatedDrug | isFdaRegulatedDevice | 
                
                # Extract dates
                primary_completion_date = study['protocolSection']['statusModule'].get('primaryCompletionDateStruct', {}).get('date', 'Unknown Date')
                study_first_post_date = study['protocolSection']['statusModule'].get('studyFirstPostDateStruct', {}).get('date', 'Unknown Date')

                # Append the data to the list as a dictionary
                data_list.append({
                    "nct_id": nct_id,
                    "brief_title": brief_title,
                    "sponsor_name": sponsor_name,
                    "sponsor_class": sponsor_class,
                    "phases": phases,
                    "has_results": has_results,
                    "overall_status": overall_status,
                    "primary_completion_date": primary_completion_date,
                    "study_first_post_date": study_first_post_date,
                    "url": "https://clinicaltrials.gov/study/" + str(nct_id)
                })

            # Check for nextPageToken and update the params or break the loop
            nextPageToken = data.get('nextPageToken')
            if nextPageToken:
                params['pageToken'] = nextPageToken  # Set the pageToken for the next request
            else:
                break  # Exit the loop if no nextPageToken is present
        else:
            print("Failed to fetch data. Status code:", response.status_code)
            break

    # Create a DataFrame from the list of dictionaries
    df = pd.DataFrame(data_list)
    df = df[(df['primary_completion_date'] != 'Unknown Date') & (df['sponsor_class'] == 'INDUSTRY')].reset_index()
    del df['index']
    df['clean_primary_completion_date'] = (
        df['primary_completion_date'].str.strip().apply(lambda x: pd.to_datetime(x, format='%Y-%m-%d', errors='coerce') 
                                                        if len(x) > 7 else pd.to_datetime(x + '-01', format='%Y-%m-%d')
                                                        )
                                        )
    df = df[df['clean_primary_completion_date'] >= pd.Timestamp.now() - pd.DateOffset(years=10)].reset_index()
    df['is_phase4'] = df['phases'].apply(lambda x: 1 if str(x).strip() == "['PHASE4']" else 0)
    del df['index']
    del df['sponsor_class']

    # Save the DataFrame to a CSV file
    df.to_csv("data/clinical_trials-completedDate_industry.csv", index=False)
    
    # Save unique sponsor names to later retrieve stock tickers
    unique_df = df['sponsor_name'].value_counts().reset_index()
    unique_df.to_csv('data/unique_sponsors.csv', index=False)

def stocks(start_date='2014-11-20', end_date='2024-11-20'):
    bio_tickers = ["GSK", "PFE"]
    yahoo_financials = YahooFinancials(bio_tickers)
    data = yahoo_financials.get_historical_price_data(start_date=start_date, 
                                                  end_date=end_date, 
                                                  time_interval='daily')
    df = pd.DataFrame({
        a: {x['formatted_date']: x['adjclose'] for x in data[a]['prices']} for a in bio_tickers})

    df.to_csv("data/{}.csv".format(str(bio_tickers)), index=False)
    return


if __name__ == "__main__":
    clinical_trials()
    # stocks()