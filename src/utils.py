import requests
import os
import pandas as pd
from datetime import datetime
from xml.etree import ElementTree as ET
from dotenv import load_dotenv
from supabase import create_client, Client

from typing import List
import os
import json
import logging
from datetime import datetime
import requests
import pandas as pd
from io import StringIO







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
    print("🎉 He terminado de insertar en Supabase.")
    # Evita que el script falle: siempre retorna con éxito
    return 0

def get_embedding(text: str) -> List[float]:
    """Generate embedding using Ollama API."""
    try:
        response = requests.post(
            "http://localhost:11434/api/embeddings",
            json={
                "model": "tazarov/all-minilm-l6-v2-f32:latest",
                "prompt": text
            }
        )
        response.raise_for_status()
        embedding = response.json().get("embedding", [])
        if not embedding:
            raise ValueError("No embedding returned")
        return embedding
    except Exception as e:
        print(f"Error generating embedding with Ollama: {e}")
        return [0] * 384  # Zero vector for all-MiniLM-L6-v2
