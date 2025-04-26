import os
import json
import logging
from datetime import datetime
import requests
import pandas as pd
from io import StringIO

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



def process_item(item, all_items, metadatos, diario_num, sumario_diario, seccion_codigo, seccion_nombre, depto_codigo, depto_nombre, epigrafe_nombre):
    # Extraer solo la URL y el tamaño en KB si los campos son dict
    def extract_url(field):
        val = item.get(field, '')
        if isinstance(val, dict):
            return val.get('url', '')
        return val

    def extract_szKBytes():
        val = item.get('url_pdf', '')
        if isinstance(val, dict):
            return int(val.get('szKBytes', 0))
        return 0

    item_data = {
        'fecha_publicacion': metadatos.get('fecha_publicacion', ''),
        'publicacion': metadatos.get('publicacion', ''),
        'diario_numero': diario_num,
        'sumario_id': sumario_diario.get('identificador', ''),
        'sumario_url_pdf': sumario_diario.get('url_pdf', ''),
        'seccion_codigo': seccion_codigo,
        'seccion_nombre': seccion_nombre,
        'departamento_codigo': depto_codigo,
        'departamento_nombre': depto_nombre,
        'epigrafe_nombre': epigrafe_nombre,
        'item_id': item.get('identificador', ''),
        'item_titulo': item.get('titulo', ''),
        'item_url_pdf': extract_url('url_pdf'),
        'item_url_html': extract_url('url_html'),
        'item_url_xml': extract_url('url_xml'),
        'szKBytes': extract_szKBytes(),
    }

    print(f"✅ Item añadido: {item_data['item_titulo'][:60]}...")
    all_items.append(item_data)

def flatten_boe_data(data):
    print("🔍 Entrando a flatten_boe_data()")
    all_items = []
    
    if 'data' not in data or 'sumario' not in data['data']:
        print("⚠️ No se encuentra 'data' o 'sumario' en el JSON")
        return all_items
    
    sumario = data['data']['sumario']
    metadatos = sumario.get('metadatos', {})
    print(f"📅 Fecha publicación: {metadatos.get('fecha_publicacion')}, Publicación: {metadatos.get('publicacion')}")
    
    for diario in sumario.get('diario', []):
        diario_num = diario.get('numero', '')
        print(f"\n🗞️ Procesando diario número: {diario_num}")
        sumario_diario = diario.get('sumario_diario', {})
        
        for seccion in diario.get('seccion', []):
            if not isinstance(seccion, dict):
                print("⛔ Sección ignorada, no es dict")
                continue

            seccion_codigo = seccion.get('codigo', '')
            seccion_nombre = seccion.get('nombre', '')
            print(f"🔸 Sección: {seccion_codigo} - {seccion_nombre}")
            
            if 'texto' in seccion and isinstance(seccion['texto'], dict) and 'departamento' in seccion['texto']:
                seccion_texto_dept = seccion['texto']['departamento']
                if not isinstance(seccion_texto_dept, list):
                    seccion_texto_dept = [seccion_texto_dept]
                    
                for departamento in seccion_texto_dept:
                    if not isinstance(departamento, dict):
                        print("⚠️ Departamento en texto no es dict")
                        continue
                    
                    depto_codigo = departamento.get('codigo', '')
                    depto_nombre = departamento.get('nombre', '')
                    print(f"    🏛️ Departamento en texto: {depto_codigo} - {depto_nombre}")
                    
                    if 'epigrafe' in departamento:
                        epigrafes = departamento['epigrafe']
                        if not isinstance(epigrafes, list):
                            epigrafes = [epigrafes]
                            
                        for epigrafe in epigrafes:
                            if not isinstance(epigrafe, dict):
                                continue
                            epigrafe_nombre = epigrafe.get('nombre', '')
                            print(f"        📌 Epígrafe: {epigrafe_nombre}")
                            
                            if 'item' in epigrafe:
                                items = epigrafe['item']
                                if not isinstance(items, list):
                                    items = [items]
                                    
                                for item in items:
                                    print(f"            📄 Procesando item con título: {item.get('titulo', '')}")
                                    if isinstance(item, dict):
                                        process_item(item, all_items, metadatos, diario_num, sumario_diario,
                                                     seccion_codigo, seccion_nombre, depto_codigo, depto_nombre, epigrafe_nombre)
            
            if 'departamento' in seccion:
                departamentos = seccion['departamento']
                if not isinstance(departamentos, list):
                    departamentos = [departamentos]

                for departamento in departamentos:
                    if not isinstance(departamento, dict):
                        continue
                    
                    depto_codigo = departamento.get('codigo', '')
                    depto_nombre = departamento.get('nombre', '')
                    print(f"    🏛️ Departamento directo: {depto_codigo} - {depto_nombre}")
                    
                    if 'texto' in departamento and isinstance(departamento['texto'], dict) and 'item' in departamento['texto']:
                        items = departamento['texto']['item']
                        if not isinstance(items, list):
                            items = [items]
                        
                        for item in items:
                            print(f"        📄 Item en texto directo: {item.get('titulo', '')}")
                            if isinstance(item, dict):
                                process_item(item, all_items, metadatos, diario_num, sumario_diario,
                                             seccion_codigo, seccion_nombre, depto_codigo, depto_nombre, 'Texto')
                    
                    if 'epigrafe' in departamento:
                        epigrafes = departamento['epigrafe']
                        if not isinstance(epigrafes, list):
                            epigrafes = [epigrafes]
                        
                        for epigrafe in epigrafes:
                            if not isinstance(epigrafe, dict):
                                continue
                            epigrafe_nombre = epigrafe.get('nombre', '')
                            print(f"        📌 Epígrafe en depto: {epigrafe_nombre}")
                            
                            if 'item' in epigrafe:
                                items = epigrafe['item']
                                if not isinstance(items, list):
                                    items = [items]
                                
                                for item in items:
                                    print(f"            📄 Item en epígrafe: {item.get('titulo', '')}")
                                    if isinstance(item, dict):
                                        process_item(item, all_items, metadatos, diario_num, sumario_diario,
                                                     seccion_codigo, seccion_nombre, depto_codigo, depto_nombre, epigrafe_nombre)
                    
                    if 'item' in departamento:
                        items = departamento['item']
                        if not isinstance(items, list):
                            items = [items]
                        
                        for item in items:
                            print(f"        📄 Item directo: {item.get('titulo', '')}")
                            if isinstance(item, dict):
                                process_item(item, all_items, metadatos, diario_num, sumario_diario,
                                             seccion_codigo, seccion_nombre, depto_codigo, depto_nombre, '')

    print(f"✅ Total de items procesados: {len(all_items)}")
    return all_items

def get_boe_data(date=None, data=None, **kwards):
    """
    Get data from the BOE API for a specific date.

    Args:
        date (datetime, optional): The date to get data for. string format {"Y%%m%d"}. Defaults to today.
        data (json, optional): The data to process. If provided, the function will not make an API request.
            Defaults to None. If data is provided, date is required.

    Returns:
        pandas.DataFrame: A DataFrame containing the flattened BOE data
    """
    mode = "local"
    if kwards:
        if "s3_bucket" in kwards:
            s3_bucket = kwards["s3_bucket"]
            mode = "lambda"
            logger.info("Running in Lambda mode with S3 bucket: %s", s3_bucket)

    if data and date:
        date_str = date

    elif data is None:
        if date is None:
            date_str = datetime.today().strftime('%Y%m%d')
        else:
            date_str = date

        url = f"https://www.boe.es/datosabiertos/api/boe/sumario/{date_str}"
        headers = {"Accept": "application/json"}

        try:
            logger.info("Fetching data from URL: %s", url)
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                logger.error("Received status code %d", response.status_code)

            data = response.json()

        except requests.exceptions.RequestException as e:
            logger.error("Error fetching data from BOE API: %s", e)
            return pd.DataFrame()

        else:
            json_output_dir = "output_json"
            output_file = f"boe_data_{date_str}.json"
            output_path = os.path.join("output_json", output_file)

            if mode == "local":
                os.makedirs(json_output_dir, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                logger.info("JSON data saved to %s", output_path)

            elif mode == "lambda":
                save_to_s3(
                    body=json.dumps(data),
                    bucket=s3_bucket,
                    key=output_path,
                    content_type='application/json'
                )
                logger.info("JSON data saved to S3 bucket %s with key %s", s3_bucket, output_path)

    flattened_data = flatten_boe_data(data)
    df = pd.DataFrame(flattened_data)

    logger.info("DataFrame created with %d rows and %d columns", df.shape[0], df.shape[1])

    csv_output_dir = "output_csv"
    csv_output_file = f"boe_data_{date_str}.csv"
    csv_output_path = os.path.join(csv_output_dir, csv_output_file)

    if mode == "local":
        os.makedirs(csv_output_dir, exist_ok=True)
        df.to_csv(csv_output_path, index=False, encoding='utf-8', sep='|')
        logger.info("CSV data saved to %s", csv_output_path)

        # Eliminar columnas no esenciales después de guardar el CSV
        campos_esenciales = [
            'fecha_publicacion',
            'diario_numero',
            'sumario_id',
            'seccion_codigo',
            'seccion_nombre',
            'departamento_codigo',
            'departamento_nombre',
            'epigrafe_nombre',
            'item_id',
            'item_titulo',
            'item_url_pdf',
            'item_url_xml',
            'szKBytes'
        ]
        df = df[campos_esenciales]

    elif mode == "lambda":
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8', sep='|')
        save_to_s3(
            body=csv_buffer.getvalue(),
            bucket=s3_bucket,
            key=csv_output_path,
            content_type='text/csv'
        )
        logger.info("CSV data saved to S3 bucket %s with key %s", s3_bucket, csv_output_path)

        # Eliminar columnas no esenciales después de guardar el CSV
        campos_esenciales = [
            'fecha_publicacion',
            'diario_numero',
            'sumario_id',
            'seccion_codigo',
            'seccion_nombre',
            'departamento_codigo',
            'departamento_nombre',
            'epigrafe_nombre',
            'item_id',
            'item_titulo',
            'item_url_pdf',
            'item_url_xml',
            szKBytes
        ]
        df = df[campos_esenciales]

    return df

def save_to_s3(body, bucket, key, content_type=None):
    """
    Save the given body to an S3 bucket with the specified key.

    Args:
        body (str): The content to save.
        bucket (str): The name of the S3 bucket.
        key (str): The key under which to save the content.
        content_type (str, optional): The content type of the file. Defaults to None.
    """
    s3 = boto3.client('s3')
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=body,
        ContentType=content_type
    )
    logger.info("File successfully uploaded to S3: s3://%s/%s", bucket, key)


