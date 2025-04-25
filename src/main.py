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

def get_chunking_strategy(row):
    if row['seccion_codigo'] == '2A' and row['epigrafe_nombre'] == 'Nombramientos':
        return 'document'
    elif row['seccion_codigo'] == '2B':
        return 'intro_and_each_list'
    elif row['seccion_codigo'] == '3' and row['departamento_nombre'] == 'Universidades':
        return 'intro_and_each_table'
    elif row['seccion_codigo'] == '5A':
        return 'each_dl_section'
    elif row['seccion_codigo'] == '5B':
        return 'blocks_and_tables'
    elif row['seccion_codigo'] == '5C':
        return 'document'
    else:
        return 'otros'


def chunk_xml_documents(df, xml_dir="output_xml"):
    """
    Procesa todos los XML en xml_dir, determina la estrategia de chunking y prepara para dividirlos.
    Imprime la estrategia seleccionada para cada documento y un resumen de conteos por tipo.
    """
    from collections import Counter

    strategy_counter = Counter()
    total = 0
    not_found = 0

    for item_id in df['item_id']:
        xml_path = os.path.join(xml_dir, f"{item_id}.xml")
        if not os.path.exists(xml_path):
            print(f"❌ No existe el XML: {xml_path}")
            not_found += 1
            continue
        row = df[df['item_id'] == item_id].iloc[0]
        strategy = get_chunking_strategy(row)
        strategy_counter[strategy] += 1
        total += 1
        xml_url = row.get('item_url_xml', 'URL no encontrada')
        print(f"Procesando {xml_path} (url: {xml_url}) con estrategia: {strategy}")

    print("\nResumen de documentos por tipo de chunking:")
    for strategy, count in strategy_counter.items():
        print(f"- {strategy}: {count}")
    if not_found > 0:
        print(f"- No encontrados: {not_found}")
    print(f"Total procesados: {total}")


def chunk_boe_5b_blocks_and_tables(xml_path, item_id, output_dir):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    texto = root.find("texto")

    chunks = []
    current_paragraphs = []

    for elem in texto:
        if elem.tag == "p":
            current_paragraphs.append(elem.text.strip() if elem.text else "")
        elif elem.tag == "table":
            # Guarda los párrafos acumulados antes de la tabla
            if current_paragraphs:
                chunk_text = "\n".join(current_paragraphs).strip()
                if chunk_text:
                    chunks.append({"type": "paragraph_block", "text": chunk_text})
                current_paragraphs = []
            # Guarda la tabla como chunk
            table_text = []
            for row in elem.findall(".//tr"):
                row_text = []
                for cell in row:
                    cell_text = "".join(cell.itertext()).strip()
                    row_text.append(cell_text)
                table_text.append(" | ".join(row_text))
            chunks.append({"type": "table", "text": "\n".join(table_text)})
    # Guarda los párrafos restantes después de la última tabla
    if current_paragraphs:
        chunk_text = "\n".join(current_paragraphs).strip()
        if chunk_text:
            chunks.append({"type": "paragraph_block", "text": chunk_text})

    # Guarda cada chunk como archivo individual en el directorio de salida
    os.makedirs(output_dir, exist_ok=True)
    for i, chunk in enumerate(chunks):
        chunk_filename = f"{item_id}_chunk_{i+1}_{chunk['type']}.txt"
        chunk_path = os.path.join(output_dir, chunk_filename)
        with open(chunk_path, "w", encoding="utf-8") as f:
            f.write(chunk["text"])
    print(f"Guardados {len(chunks)} chunks para {item_id}")


def chunk_all_5b(df, xml_dir, output_dir):
    df_5b = df[df['seccion_codigo'] == '5B']
    for idx, row in df_5b.iterrows():
        item_id = row['item_id']
        xml_path = os.path.join(xml_dir, f"{item_id}.xml")
        if os.path.exists(xml_path):
            chunk_boe_5b_blocks_and_tables(xml_path, item_id, output_dir)
        else:
            print(f"No se encontró el XML: {xml_path}")


def chunk_boe_5b_blocks_and_tables_markdown(xml_path, item_id, output_dir):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    texto = root.find("texto")

    chunks = []
    current_paragraphs = []
    all_tables_md = []

    for elem in texto:
        if elem.tag == "p":
            current_paragraphs.append(elem.text.strip() if elem.text else "")
        elif elem.tag == "table":
            # Si hay un título justo antes de la tabla, lo incluimos
            table_title = ""
            if current_paragraphs:
                table_title = "\n".join(current_paragraphs).strip()
                current_paragraphs = []
            # Extrae la tabla en formato markdown
            table_rows = []
            for row in elem.findall(".//tr"):
                row_cells = []
                for cell in row:
                    cell_text = "".join(cell.itertext()).strip()
                    row_cells.append(cell_text)
                table_rows.append("| " + " | ".join(row_cells) + " |")
            table_md = "\n".join(table_rows)
            if table_title:
                all_tables_md.append(f"**{table_title}**\n{table_md}")
            else:
                all_tables_md.append(table_md)

    # Chunk de párrafos (si hay texto fuera de tablas)
    if current_paragraphs:
        chunk_text = "\n".join(current_paragraphs).strip()
        if chunk_text:
            chunks.append({"type": "paragraph_block", "text": chunk_text})

    # Chunk único con todas las tablas en markdown
    if all_tables_md:
        chunks.append({"type": "all_tables", "text": "\n\n---\n\n".join(all_tables_md)})

    # Guarda cada chunk como markdown
    os.makedirs(output_dir, exist_ok=True)
    for i, chunk in enumerate(chunks):
        chunk_filename = f"{item_id}_chunk_{i+1}_{chunk['type']}.md"
        chunk_path = os.path.join(output_dir, chunk_filename)
        with open(chunk_path, "w", encoding="utf-8") as f:
            f.write(chunk["text"])
    print(f"Guardados {len(chunks)} chunks markdown para {item_id}")


def chunk_all_5b_markdown(df, xml_dir, output_dir):
    df_5b = df[df['seccion_codigo'] == '5B']
    for idx, row in df_5b.iterrows():
        item_id = row['item_id']
        xml_path = os.path.join(xml_dir, f"{item_id}.xml")
        if os.path.exists(xml_path):
            chunk_boe_5b_blocks_and_tables_markdown(xml_path, item_id, output_dir)
        else:
            print(f"No se encontró el XML: {xml_path}")


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
        except Exception as e:
            print(f"🚨 Error descargando {url}: {e}")

    # Llamada a chunk_xml_documents para analizar los XML descargados
    chunk_xml_documents(df, xml_dir=xml_output_dir)
    
    # Llamada a chunk_all_5b para procesar todos los documentos 5B
    chunk_all_5b(df, xml_output_dir, "chunks")
    
    # Llamada a chunk_all_5b_markdown para procesar todos los documentos 5B en markdown
    chunk_all_5b_markdown(df, xml_output_dir, "chunks_markdown")
    return df

if __name__ == "__main__":
    main()