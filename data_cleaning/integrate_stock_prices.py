import pandas as pd
import pymongo
import yfinance as yf
import requests
from typing import Optional, List, Dict
import os
from dotenv import load_dotenv

MONGO_URI = "mongodb://localhost:27017/"  # Default MongoDB location on local
db_name = "clinical_trials_db"
collection_name = "studies"

def main():
    print("Setting up MongoDB")
    client = pymongo.MongoClient(MONGO_URI)
    db = client[db_name]
    collection = db[collection_name]

    sponsor_pipeline = [
      {
        "$match": {
          "protocolSection.sponsorCollaboratorsModule.leadSponsor.class": "INDUSTRY"
        }
      },
      {
        "$group": {
          "_id": "$protocolSection.sponsorCollaboratorsModule.leadSponsor.name",
          "sponsor_num_trials": { "$sum": 1 }
        }
      },
      {
        "$sort": {
          "sponsor_num_trials": -1
        }
      },
      {
        "$project": {
          "company_ct": "$_id",
          "sponsor_num_trials": 1,
          "_id": 0
        }
      }
    ]

    collab_pipeline = [
      {
        "$unwind": "$protocolSection.sponsorCollaboratorsModule.collaborators"
      },
      {
        "$match": {
          "protocolSection.sponsorCollaboratorsModule.collaborators.class": "INDUSTRY"
        }
      },
      {
        "$group": {
          "_id": "$protocolSection.sponsorCollaboratorsModule.collaborators.name",
          "collab_num_trials": { "$sum": 1 }
        }
      },
      {
        "$sort": {
          "collab_num_trials": -1
        }
      },
      {
        "$project": {
          "company_ct": "$_id",
          "collab_num_trials": 1,
          "_id": 0
        }
      }
    ]

    print("Running pipelines")
    # collab_result = list(collection.aggregate(collab_pipeline))
    sponsor_result = list(collection.aggregate(sponsor_pipeline))

    df_final = pd.DataFrame(sponsor_result)
    # df_collab = pd.DataFrame(collab_result)

    # Write DataFrames to CSV
    output_dir = "./data_cleaning/processed_data/"
    df_final.to_csv(f"{output_dir}sponsor_data.csv", index=False)
    # df_collab.to_csv(f"{output_dir}collaborator_data.csv", index=False)

    # Join on public_company_potential
    # df_final = df_final.join(df_collab, on="company_ct", how="outer").fillna(0)
    # df_final["total_num_trials"] = df_final["sponsor_num_trials"] + df_final["collab_num_trials"]
    # df_final.to_csv(f"{output_dir}merged_data.csv", index=False)

    return df_final

MANUAL_MAPPING = {
    "Pfizer": "PFE",
    "Johnson & Johnson": "JNJ",
    "Eli Lilly and Company": "LLY",
    "Merck": "MRK",
    "AstraZeneca": "AZN",
    "GlaxoSmithKline": "GSK",
    "Novartis": "NVS",
    "Amgen": "AMGN",
    "Bristol-Myers Squibb": "BMY",
    "Gilead Sciences": "GILD",
    "Regeneron Pharmaceuticals": "REGN",
    "Biogen": "BIIB",
    "Vertex Pharmaceuticals": "VRTX",
    "Moderna": "MRNA",
    "Abbott": "ABT",
    "Takeda": "TAK",
    "Bayer": "BAYRY",
    "Teva Pharmaceuticals": "TEVA",
    "Novo Nordisk": "NVO",
    "Sanofi": "SNY",
    "Capricor Inc.": "CAPR",
    "Supernus Pharmaceuticals, Inc.": "SUPN",
    "Eyenovia Inc.": "EYEN",
    "Johnson & Johnson Vision Care, Inc.": "JNJ",
    "ViiV Healthcare": None,
    "Takeda": "TAK",
    "Pfizer": "PFE",
    "Santen Inc.": "SNPHY",
    "Alexion Pharmaceuticals, Inc.": "ALXN",
    "Merck Sharp & Dohme LLC": "MRK",
    "Eli Lilly and Company": "LLY",
    "AstraZeneca": "AZN",
}

def search_ticker_symbol(company_name: str) -> Optional[str]:
    """
    Search for a company's ticker symbol using the Alpha Vantage API.
    You need to sign up for a free API key at https://www.alphavantage.co/
    """

    load_dotenv()
    API_KEY = os.getenv("alpha_vantage_api_key")
    base_url = "https://www.alphavantage.co/query"
    function = "SYMBOL_SEARCH"

    params = {
        "function": function,
        "keywords": company_name,
        "apikey": API_KEY
    }

    try:
        response = requests.get(base_url, params=params)
        data = response.json()

        if "bestMatches" in data and len(data["bestMatches"]) > 0:
            return data["bestMatches"][0]["1. symbol"]
    except Exception as e:
        print(f"Error searching for {company_name}: {e}")

    return None

def get_ticker(company_name: str) -> Optional[str]:
    # Check manual mapping first
    if company_name in MANUAL_MAPPING:
        return MANUAL_MAPPING[company_name]

    try:
        # Try exact match first
        ticker = yf.Ticker(company_name)
        info = ticker.info
        if 'symbol' in info:
            return info['symbol']

        # If exact match fails, try search
        search = yf.Ticker(company_name.split()[0])  # Use first word of company name
        if 'symbol' in search.info:
            return search.info['symbol']

        # If yfinance fails, try Alpha Vantage API
        alpha_vantage_result = search_ticker_symbol(company_name)
        if alpha_vantage_result:
            return alpha_vantage_result

    except Exception as e:
        print(f"Could not find ticker for {company_name}: {e}")

    return None

def process_companies(companies: List[str]) -> Dict[str, Optional[str]]:
    company_ticker_map = {}
    for company in companies:
        ticker = get_ticker(company)
        company_ticker_map[company] = ticker
        if ticker:
            print(f"Found ticker for {company}: {ticker}")
        else:
            print(f"No ticker found for: {company}")
    return company_ticker_map


if __name__ == "__main__":
    main()
