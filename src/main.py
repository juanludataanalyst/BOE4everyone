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
    get_embedding,  # Importa la función para embeddings
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
        children = list(elem)
        i = 0
        while i < len(children):
            if children[i].tag == "dt":
                term = "".join(children[i].itertext()).strip()
                dl_lines.append(f"**{term}**")
                # Busca el siguiente elemento y verifica si es un dd
                if i + 1 < len(children) and children[i + 1].tag == "dd":
                    definition = "".join(children[i + 1].itertext()).strip()
                    dl_lines.append(f": {definition}")
                    i += 1  # Saltar el dd ya procesado
            i += 1
        return "\n".join(dl_lines)
    return ""


def chunk_boe_markdown(xml_path, item_id, output_dir, max_tokens=1000, metadata=None):
    """
    Estrategia de chunking:
    - Convierte cada elemento estructural (<p>, <table>, <ul>, <ol>, <dl>, etc.) en un bloque markdown.
    - Nunca parte un chunk en medio de un bloque: los bloques siempre se mantienen completos.
    - Acumula bloques completos hasta que el límite de tokens (por defecto 1000) se supera.
    - Los documentos pequeños (<= max_tokens) se guardan como un solo chunk.
    - Nomenclatura: <item_id>.md si es un único chunk, o <item_id>_chunkN.md si hay varios.
    Además, inserta cada chunk en la tabla boe_chunks de Supabase inmediatamente tras generarlo.
    """
    import os
    import requests
    import json
    from supabase import create_client, Client
    from dotenv import load_dotenv

    # Inicializa Supabase solo una vez
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    supabase: Client = create_client(url, key)

    tree = ET.parse(xml_path)
    root = tree.getroot()
    texto = root.find("texto")
    if texto is None:
        print(f"No se encontró <texto> en {xml_path}")
        return

    blocks = []
    for elem in texto:
        block = xml_block_to_markdown(elem)
        if block.strip():
            blocks.append(block)

    chunks = []
    current_chunk = []
    current_tokens = 0
    for block in blocks:
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
        if len(chunks) == 1:
            chunk_filename = f"{item_id}.md"
            chunk_id = item_id
        else:
            chunk_filename = f"{item_id}_chunk{i+1}.md"
            chunk_id = f"{item_id}_chunk{i+1}"
        chunk_path = os.path.join(output_dir, chunk_filename)
        with open(chunk_path, "w", encoding="utf-8") as f:
            f.write(chunk_text)
        embedding = get_embedding(chunk_text)
        print(f"🔹 Embedding para {chunk_filename}: {embedding[:8]}... (dim={len(embedding)})")
        print(f"✅ Guardado chunk: {chunk_filename} (tokens: {count_tokens(chunk_text)}) - Bloques completos, nunca partidos.")

        # Inserta el chunk en Supabase
        data = {
            "item_id": item_id,
            "chunk_number": i + 1,
            "chunk_id": chunk_id,
            "chunk_text": chunk_text,
            "embedding": embedding,
            "metadata": metadata or {},
        }
        try:
            resp = supabase.table("boe_chunks").insert(data).execute()
            if hasattr(resp, "status_code") and resp.status_code == 201:
                print(f"✅ Insertado chunk {chunk_id} en Supabase")
            else:
                print(f"❌ Error insertando chunk {chunk_id}: {resp}")
        except Exception as e:
            print(f"🚨 Excepción insertando chunk {chunk_id}: {e}")
    print(f"Guardados {len(chunks)} chunk(s) markdown para {item_id}")


def chunk_all_boe(df, xml_dir, output_dir, max_tokens=1000):
    for idx, row in df.iterrows():
        item_id = row['item_id']
        xml_path = os.path.join(xml_dir, f"{item_id}.xml")
        if not os.path.exists(xml_path):
            print(f"No se encontró el XML: {xml_path}")
            continue
        chunk_boe_markdown(xml_path, item_id, output_dir, max_tokens, metadata=row.to_dict())


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

    # Llamada a chunk_all_boe para procesar todos los documentos
    chunk_all_boe(df, xml_output_dir, "chunks", max_tokens=1000)



    
    return df

if __name__ == "__main__":
    main()