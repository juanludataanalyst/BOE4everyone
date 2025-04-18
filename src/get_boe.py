from process_boe import flatten_boe_data
import os
import json
from datetime import datetime
import requests
import pandas as pd

def get_boe_data(date=None, data=None):
    """
    Get data from the BOE API for a specific date.
    
    Args:
        date (datetime, optional): The date to get data for. Defaults to today.
        
    Returns:
        pandas.DataFrame: A DataFrame containing the flattened BOE data
    """

    if data and date:
        date_str = date

    elif date is None:
        date = datetime.now()
    
        # Format date as YYYYMMDD
        date_str = date.strftime('%Y%m%d')
        
        # Make the API request
        url = f"https://www.boe.es/datosabiertos/api/boe/sumario/{date_str}"
        headers = {"Accept": "application/json"}
        
        try:
            response = requests.get(url, headers=headers)
            #response.raise_for_status()  # Raise an exception for HTTP errors
            if response.status_code != 200:
                print(f"Error: Received status code {response.status_code}")
                return pd.DataFrame()
            
            data = response.json()
            # Save the response to a JSON file
            json_output_dir = "output_json"
            output_file = f"boe_data_{date.strftime('%Y%m%d')}.json"
            output_path = os.path.join("output_json", output_file)
            os.makedirs(json_output_dir, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"Data saved to {output_path}")
        
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from BOE API: {e}")
            return pd.DataFrame()


    # Process the nested structure
    flattened_data = flatten_boe_data(data)
    
    # Convert to DataFrame
    df = pd.DataFrame(flattened_data)

    # Save the DataFrame to a CSV file
    csv_output_dir = "output_csv"
    os.makedirs(csv_output_dir, exist_ok=True)
    csv_output_file = f"boe_data_{date_str}.csv"
    csv_output_path = os.path.join(csv_output_dir, csv_output_file)
    df.to_csv(csv_output_path, index=False, encoding='utf-8', sep='|')
    print(f"Data saved to {csv_output_path}")
    
    return df

if __name__ == "__main__":
    # Example usage
    df = get_boe_data()
    print("completed")