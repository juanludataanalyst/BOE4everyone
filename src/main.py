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


def xml_block_to_markdown(elem):
    if elem.tag == "p":
        return elem.text.strip() if elem.text else ""
    elif elem.tag == "table":
        table_rows = []
        for row in elem.findall(".//tr"):
            row_cells = []
            for cell in row:
                cell_text = "".join(cell.itertext()).strip()
                row_cells.append(cell_text)
            table_rows.append("| " + " | ".join(row_cells) + " |")
        return "\n".join(table_rows)
    elif elem.tag in ("ul", "ol"):
        items = []
        for li in elem.findall(".//li"):
            li_text = "".join(li.itertext()).strip()
            items.append(f"- {li_text}")
        return "\n".join(items)
    elif elem.tag == "dl":
        dl_lines = []
        for dt in elem.findall("dt"):
            term = "".join(dt.itertext()).strip()
            dl_lines.append(f"**{term}**")
            dd = dt.getnext()
            if dd is not None and dd.tag == "dd":
                definition = "".join(dd.itertext()).strip()
                dl_lines.append(f": {definition}")
        return "\n".join(dl_lines)
    return ""


def chunk_boe_universal_markdown(xml_path, item_id, output_dir, max_tokens=500):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    texto = root.find("texto")
    if texto is None:
        print(f"No se encontró <texto> en {xml_path}")
        return

    md_blocks = []
    for elem in texto:
        md = xml_block_to_markdown(elem)
        if md:
            md_blocks.append(md)

    # Chunking universal
    chunks = []
    current_chunk = []
    current_tokens = 0
    for block in md_blocks:
        block_tokens = count_tokens(block)
        if current_tokens + block_tokens > max_tokens and current_chunk:
            chunks.append("\n\n".join(current_chunk))
            current_chunk = [block]
            current_tokens = block_tokens
        else:
            current_chunk.append(block)
            current_tokens += block_tokens
    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    os.makedirs(output_dir, exist_ok=True)
    for i, chunk_text in enumerate(chunks):
        chunk_filename = f"{item_id}_chunk_{i+1}_universal.md"
        chunk_path = os.path.join(output_dir, chunk_filename)
        with open(chunk_path, "w", encoding="utf-8") as f:
            f.write(chunk_text)
    print(f"Guardados {len(chunks)} chunks universales markdown para {item_id}")


def chunk_boe_5a_dl_sections(xml_path, item_id, output_dir, max_tokens=500):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    texto = root.find("texto")
    if texto is None:
        print(f"No se encontró <texto> en {xml_path}")
        return

    dl_chunks = []
    for dl in texto.findall("dl"):
        dl_text = []
        for elem in dl:
            if elem.tag == "dt":
                term = "".join(elem.itertext()).strip()
                dl_text.append(f"**{term}**")
            elif elem.tag == "dd":
                definition = "".join(elem.itertext()).strip()
                dl_text.append(f": {definition}")
        chunk_text = "\n".join(dl_text)
        if chunk_text.strip():
            dl_chunks.append(chunk_text)

    os.makedirs(output_dir, exist_ok=True)
    for i, chunk_text in enumerate(dl_chunks):
        chunk_filename = f"{item_id}_chunk_{i+1}_5A_dl.md"
        chunk_path = os.path.join(output_dir, chunk_filename)
        with open(chunk_path, "w", encoding="utf-8") as f:
            f.write(chunk_text)
    print(f"Guardados {len(dl_chunks)} chunks 5A (por <dl>) para {item_id}")


def chunk_all_boe(df, xml_dir, output_dir_universal, output_dir_5a, max_tokens=500):
    for idx, row in df.iterrows():
        item_id = row['item_id']
        seccion_codigo = row.get('seccion_codigo', '')
        xml_path = os.path.join(xml_dir, f"{item_id}.xml")
        if not os.path.exists(xml_path):
            print(f"No se encontró el XML: {xml_path}")
            continue

        # Excepción: 5A (contratación pública)
        if seccion_codigo == '5A':
            chunk_boe_5a_dl_sections(xml_path, item_id, output_dir_5a, max_tokens)
        else:
            chunk_boe_universal_markdown(xml_path, item_id, output_dir_universal, max_tokens)


try:
    import tiktoken
    def count_tokens(text):
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
except ImportError:
    def count_tokens(text):
        # Aproximación: 1 token ~= 0.75 palabras
        return int(len(text.split()) / 0.75)


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
    
    # Llamada a chunk_all_boe para procesar todos los documentos
    chunk_all_boe(df, xml_output_dir, "chunks_universal", "chunks_5A", max_tokens=500)
    return df

if __name__ == "__main__":
    main()