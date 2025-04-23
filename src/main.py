#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import requests
from datetime import datetime
from get_boe import get_boe_data
from xml.etree import ElementTree as ET

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

def parse_xml_from_url(url):
    """
    Descarga y parsea un XML desde una URL, extrayendo el texto del nodo <texto> y sus hijos.
    Devuelve el texto plano concatenado.
    """
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            tree = ET.fromstring(response.content)
            texto_element = tree.find('.//texto')
            if texto_element is not None:
                texto_content = []
                for elem in texto_element.iter():
                    if elem.tag != 'texto' and elem.text:
                        texto_content.append(elem.text.strip())
                return ' '.join(texto_content).replace('|', '&#124;')
            else:
                print(f"⚠️ No se encontró el nodo <texto> en el XML de {url}")
                return ''
        else:
            print(f"❌ Error {response.status_code} al descargar el XML: {url}")
            return ''
    except Exception as e:
        print(f"🚨 Excepción al parsear el XML: {str(e)}")
        return ''

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
    return df


if __name__ == "__main__":
    main()