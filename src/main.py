#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from datetime import datetime
from get_boe import get_boe_data

def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description='Extract data from BOE API')
    parser.add_argument(
        '--date',
        type=lambda s: datetime.strptime(s, '%Y-%m-%d'),
        help='Date to extract data for in format YYYY-MM-DD'
    )
    
    return parser.parse_args()

def main(date=None):
    """Main function to run the ETL process"""
    args = parse_arguments()

    # If date is provided as an argument, use it; otherwise, use the default date
    if args.date:
        date = args.date
    elif date:
        date = datetime.strptime(date, '%Y-%m-%d')
    elif date == None:
        date = datetime.now()
    
    print(f"Recibiendo el BOE con fecha: {date.strftime('%Y-%m-%d')}")
    
    df = get_boe_data(date)
    return df


if __name__ == "__main__":
    main(
        date="2025-04-17",  # Example date, can be replaced with a dynamic date
    )
    