#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import requests
import os
import pandas as pd
from datetime import datetime
from get_boe import get_boe_data
from xml.etree import ElementTree as ET
from dotenv import load_dotenv
from supabase import create_client, Client

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

def preparar_dataframe_boe(df):
    # Eliminar columna item_url_pdf si existe
    if 'item_url_pdf' in df.columns:
        df = df.drop(columns=['item_url_pdf'])
    # Convertir fecha_publicacion a string 'YYYY-MM-DD'
    if 'fecha_publicacion' in df.columns:
        df['fecha_publicacion'] = pd.to_datetime(df['fecha_publicacion'], errors='coerce').dt.strftime('%Y-%m-%d')
    # Convertir diario_numero y departamento_codigo a enteros
    for col in ['diario_numero', 'departamento_codigo']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
    return df

def insertar_boe_metadatos_supabase(df):
    """
    Inserta los registros del DataFrame en la tabla boe_metadatos de Supabase.
    """
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    supabase: Client = create_client(url, key)
    print("SERVICE_KEY:", os.getenv("SUPABASE_SERVICE_KEY"))
    # Preprocesar el DataFrame según los nuevos tipos y columnas
    df = preparar_dataframe_boe(df)
    data = df.to_dict(orient="records")
    for i in range(0, len(data), 100):
        batch = data[i:i+100]
        try:
            resp = supabase.table("boe_metadatos").insert(batch).execute()
            if resp.data:
                print(f"✅ Insertados {len(resp.data)} registros en boe_metadatos.")
            else:
                print(f"❌ Error insertando lote. Respuesta: {resp}")
        except Exception as e:
            # Maneja duplicados sin parar la ejecución
            if 'duplicate key value violates unique constraint' in str(e):
                print(f"⚠️ Lote con duplicados no insertado (constraint UNIQUE): {e}")
            else:
                print(f"🚨 Error inesperado insertando lote: {e}")
    return

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