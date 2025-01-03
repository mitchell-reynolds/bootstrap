import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests
import os
from dotenv import load_dotenv

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

        print(data)

        if "bestMatches" in data and len(data["bestMatches"]) > 0:
            return data["bestMatches"][0]["1. symbol"]
    except Exception as e:
        print(f"Error searching for {company_name}: {e}")

    return None

def get_ticker(company_name: str) -> Optional[str]:

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

    # Merge the dictionaries, with the df_dict taking precedence and removing dupes (case sensitive)
    df_lookup = pd.read_csv("./data_cleaning/processed_data/stock_lkup.csv")
    df_dict = dict(zip(df_lookup['company_ct'], df_lookup['stock_ticker']))
    MANUAL_MAPPING = {**MANUAL_MAPPING, **df_dict}
    MANUAL_MAPPING = dict(MANUAL_MAPPING)

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

def expand_stocks():
    unique_sponsors = pd.read_csv("./data_cleaning/processed_data/sponsor_data.csv")
    unique_sponsors = unique_sponsors[unique_sponsors["sponsor_num_trials"] >= 30]
    unique_sponsors = unique_sponsors["company_ct"].unique().tolist()

    results = process_companies(unique_sponsors)

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

    # Merge the dictionaries, with the df_dict taking precedence and removing dupes (case sensitive)
    df_lookup = pd.read_csv("./data_cleaning/processed_data/stock_lkup.csv")
    df_dict = dict(zip(df_lookup['company_ct'], df_lookup['stock_ticker']))
    MANUAL_MAPPING = {**MANUAL_MAPPING, **df_dict}
    results = {**MANUAL_MAPPING, **results}
    results = dict(results)

    # Drop companies with no ticker
    results = {k: v for k, v in results.items() if v is not None}

    final_df = pd.DataFrame.from_dict(results, orient='index', columns=['stock_ticker'])
    final_df.index.name = 'company_ct'
    
    return final_df

def main():
    
    df_lookup = expand_stocks().reset_index()
    
    # Define time range
    end_date = datetime.today()
    start_date = end_date - timedelta(days=365*11)

    result_dfs = []
    for _, row in df_lookup.iterrows():
        ticker = row["stock_ticker"]
        company_ct = row["company_ct"]
        data = yf.download(ticker, start=start_date, end=end_date)
        if not data.empty:
            temp = data[["Close"]].reset_index()
            temp["company_ct"] = company_ct
            temp["ticker"] = ticker
            temp.columns = ["date_stock", "closing_price", "company_ct", "ticker"]
            result_dfs.append(temp[["date_stock", "company_ct", "ticker", "closing_price"]])

    final_df = pd.concat(result_dfs, ignore_index=True)
    final_df.to_csv("./data_ingest/raw_data/merged_stock_data_updated.csv", index=False)

if __name__ == "__main__":
    main()
