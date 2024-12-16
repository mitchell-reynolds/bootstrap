import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

def main():
    # Load lookup DataFrame
    df_lookup = pd.read_csv("./data_cleaning/processed_data/stock_lkup.csv")

    # Define time range
    end_date = datetime.today()
    start_date = end_date - timedelta(days=365*10)

    result_dfs = []
    for _, row in df_lookup.iterrows():
        ticker = row["stock_ticker"]
        company_ct = row["company_ct"]
        data = yf.download(ticker, start=start_date, end=end_date)
        if not data.empty:
            temp = data[["Close"]].reset_index()
            temp["company_ct"] = company_ct
            temp.columns = ["date_stock", "closing_price", "company_ct"]
            result_dfs.append(temp[["date_stock", "company_ct", "closing_price"]])

    final_df = pd.concat(result_dfs, ignore_index=True)
    final_df.to_csv("./data_ingest/raw_data/merged_stock_data.csv", index=False)

if __name__ == "__main__":
    main()
