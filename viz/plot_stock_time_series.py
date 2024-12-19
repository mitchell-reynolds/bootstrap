import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import argparse
import os

def load_data(stock_path, drugs_path):
    """Load and preprocess stock and drug data"""
    stocks = pd.read_csv(stock_path)
    drugs = pd.read_csv(drugs_path)
    
    # Convert date columns
    drugs['fda_date'] = pd.to_datetime(drugs['fda_date'])
    drugs['ct_date'] = pd.to_datetime(drugs['ct_date'])
    stocks['date_stock'] = pd.to_datetime(stocks['date_stock'])
    
    return stocks, drugs

def filter_drugs(drugs_df, limit_to_companies_with_X_or_fewer_drugs=1000):
    """Filter and sample drugs data"""
    filtered = drugs_df.dropna(subset=['fda_company', 'fda_date', 'ct_date', 'ct_phase', 'matched_drug_names'])
    filtered = filtered.sort_values(by=['ct_date']).drop_duplicates(subset=['fda_id'], keep='last')
    filtered = filtered[filtered['fda_company'].isin(
        filtered['fda_company'].value_counts()[filtered['fda_company'].value_counts() <= limit_to_companies_with_X_or_fewer_drugs].index
    )]
    
    return filtered

def create_plotly_figure(company_stocks, row):
    """Create a Plotly figure for a single drug"""
    
    colors = ['#1ABC9C', '#F4D03F', '#9B59B6', '#3498DB', '#2ECC71', '#E74C3C', '#95A5A6']
    fig = go.Figure()
    
    # Add stock price line
    fig.add_trace(
        go.Scatter(
            x=company_stocks['date_stock'],
            y=company_stocks['closing_price'],
            line=dict(color=colors[0]),  # Light teal color
            name='Stock Price'
        )
    )
    
    # Add FDA approval line
    fig.add_vline(
        x=row['fda_date'].timestamp() * 1000,
        line_dash="dash",
        line_color=colors[1],
        annotation_text=f'FDA Approval Date on {row["fda_date"].strftime("%Y-%m-%d")}'
    )
    
    # Add CT date line if within range
    start_date = row['fda_date'] - pd.Timedelta(days=365)
    end_date = row['fda_date'] + pd.Timedelta(days=20)
    ct_phase = str(row.ct_phase).replace("'", "").replace("[", "").replace("]", "")
    if start_date <= row['ct_date'] <= end_date:
        fig.add_vline(
            x=row['ct_date'].timestamp() * 1000,
            line_dash="dash",
            line_color=colors[2],
            annotation_text=f'{ct_phase} completed on {row["ct_date"].strftime("%Y-%m-%d")}'
        )
    
    # Update layout with stock ticker and dollar format
    ticker = company_stocks['ticker'].iloc[0] if not company_stocks['ticker'].empty else 'Unknown'
    fig.update_layout(
        title={
            'text': (f'{row["fda_company"]} ({ticker}): {row["matched_drug_names"]}<br>' +
                    f'<a href="https://www.google.com/search?q=fda%20approval%20{row["fda_company"]}%20{row["matched_drug_names"]}">Google Search for FDA</a> | ' +
                    f'<a href="https://clinicaltrials.gov/study/{row["ct_id"]}">Clinical Trial</a>'),
            'xanchor': 'center',
            'x': 0.5
        },
        yaxis_title='Stock Price ($)',
        yaxis=dict(
            tickprefix="$",
            tickformat=",.2f"
        ),
        showlegend=True,
        template='plotly_dark'
    )
    
    return fig

def create_seaborn_plot(company_stocks, row):
    """Create a Seaborn plot for a single drug and save to file"""
    plt.figure(figsize=(12, 6))
    sns.lineplot(data=company_stocks, x='date_stock', y='closing_price')
    
    # Add FDA approval line
    plt.axvline(x=row['fda_date'], color='darkred', linestyle='--', 
                label=f'FDA Approval Date on {row["fda_date"].strftime("%Y-%m-%d")}')
    
    # Add CT date line if within range
    start_date = row['fda_date'] - pd.Timedelta(days=365)
    end_date = row['fda_date'] + pd.Timedelta(days=20)
    ct_phase = str(row.ct_phase).replace("'", "").replace("[", "").replace("]", "")
    if start_date <= row['ct_date'] <= end_date:
        plt.axvline(x=row['ct_date'], color='midnightblue', linestyle='--',
                    label=f'{ct_phase} completed on {row["ct_date"].strftime("%Y-%m-%d")}')
    
    # Add ticker to title
    ticker = company_stocks['ticker'].iloc[0] if not company_stocks['ticker'].empty else 'Unknown'
    plt.title(f'{row["fda_company"]} ({ticker}): {row["matched_drug_names"]} \n FDA Application: {row["fda_id"]} | Clinical Trial: {row["ct_id"]}')
    
    plt.xlabel('')
    plt.ylabel('Stock Price ($)')
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', color='grey')
    plt.legend()
    
    # Format y-axis ticks to show dollars
    ax = plt.gca()
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.2f}'))
    
    plt.tight_layout()
    
    # Create figures directory if it doesn't exist
    os.makedirs('./viz/figures', exist_ok=True)
    
    # Create filename using relevant information
    clean_drug_name = row["matched_drug_names"].replace('/', '_').replace(' ', '_').replace(',', '')
    filename = f'./viz/figures/{row["fda_company"]}_{ticker}_{clean_drug_name}_{row["ct_id"]}.png'
    
    # Save figure
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
    
    return filename

def main():
    parser = argparse.ArgumentParser(description='Plot stock time series data')
    stock_path = './data_ingest/raw_data/merged_stock_data.csv'
    drugs_path = './data_cleaning/processed_data/filtered_drugs.csv'
    parser.add_argument('--plots', choices=['plotly', 'seaborn', 'both'], default='seaborn',
                        help='Type of plot to generate')
    parser.add_argument('--limit', type=int, default=10,
                        help='Limit to companies with X or fewer drugs')
    args = parser.parse_args()
    
    # Load and process data
    stocks, drugs = load_data(stock_path, drugs_path)
    filtered_drugs = filter_drugs(drugs, args.limit)
    
    # Iterate over each drug entry
    for _, row in filtered_drugs.iterrows():
        start_date = row['fda_date'] - pd.Timedelta(days=180)
        end_date = row['fda_date'] + pd.Timedelta(days=10)
        
        # Filter stock data
        company_stocks = stocks[
            (stocks['company_ct'] == row['fda_company']) & 
            (stocks['date_stock'] >= start_date) & 
            (stocks['date_stock'] <= end_date)
        ]
        
        if len(company_stocks) == 0:
            continue
            
        if args.plots in ['plotly', 'both']:
            fig = create_plotly_figure(company_stocks, row)
            fig.show()
            
        if args.plots in ['seaborn', 'both']:
            filename = create_seaborn_plot(company_stocks, row)

if __name__ == "__main__":
    main()
