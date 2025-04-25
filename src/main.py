#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import requests
import os
import pandas as pd
from datetime import datetime
from xml.etree import ElementTree as ET
from dotenv import load_dotenv
from supabase import create_client, Client

from utiils_get_data import get_boe_data

from utils import (
    insertar_boe_metadatos_supabase, 
    parse_xml_from_url, 
    )


def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description='Extract data from BOE API')
    parser.add_argument(
        '--date',
        type=lambda s: datetime.strptime(s, '%Y-%m-%d').strftime('%Y%m%d'),
        help='Date to extract data for in format YYYY-MM-DD'
    )
    
    return parser.parse_args()

def main():
    """Main function to run the ETL process from a python console. --date YYYY-MM-DD can be passed to retrive specific date"""
    args = parse_arguments()

    # If date is provided as an argument, use it; otherwise, use the default date
    if args.date:
        date = args.date
    else:
        date = datetime.today().strftime('%Y%m%d')
    
    print(f"Recibiendo el BOE con fecha: {date}")
    
    df = get_boe_data(date=date)
    print("\nDataFrame reducido tras eliminar campos no esenciales:")
    print(df.head(10))

    # Llama a la función para insertar en Supabase
    insertar_boe_metadatos_supabase(df)


    

    # Crear carpeta de salida si no existe
    xml_output_dir = "output_xml"
    os.makedirs(xml_output_dir, exist_ok=True)

    # Descargar y guardar cada XML
    for idx, row in df.iterrows():
        url = row['item_url_xml']
        item_id = row['item_id']
        if not url or not item_id:
            continue
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                xml_path = os.path.join(xml_output_dir, f"{item_id}.xml")
                with open(xml_path, "wb") as f:
                    f.write(response.content)
                print(f"✅ Guardado: {xml_path}")
            else:
                print(f"❌ Error {response.status_code} al descargar {url}")
        except Exception as e:
            print(f"🚨 Excepción al descargar {url}: {str(e)}")
    return df

if __name__ == "__main__":
    main()