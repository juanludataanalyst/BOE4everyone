import json
import boto3
from pandas import DataFrame
from io import StringIO
import os

def flatten_boe_data(data):
    """
    Process the nested BOE data structure and convert to a list of flattened dictionaries.
    
    Args:
        data (dict): The BOE API response data
        
    Returns:
        list: A list of dictionaries containing flattened data
    """
    all_items = []
    
    # Check if we have a sumario
    if 'data' not in data or 'sumario' not in data['data']:
        return all_items
    
    sumario = data['data']['sumario']
    metadatos = sumario.get('metadatos', {})
    
    # Process each diario
    for diario in sumario.get('diario', []):
        diario_num = diario.get('numero', '')
        sumario_diario = diario.get('sumario_diario', {})
        
        # Process each section
        for seccion in diario.get('seccion', []):
            # Handle the case where seccion is a dict, not a list
            if not isinstance(seccion, dict):
                continue
                
            seccion_codigo = seccion.get('codigo', '')
            seccion_nombre = seccion.get('nombre', '')
            
            # Check if seccion has texto field with items
            if 'texto' in seccion and isinstance(seccion['texto'], dict) and 'departamento' in seccion['texto']:
                seccion_texto_dept = seccion['texto']['departamento']
                if not isinstance(seccion_texto_dept, list):
                    seccion_texto_dept = [seccion_texto_dept]
                    
                for departamento in seccion_texto_dept:
                    if not isinstance(departamento, dict):
                        continue
                        
                    depto_codigo = departamento.get('codigo', '')
                    depto_nombre = departamento.get('nombre', '')
                    
                    # Process epigrafes in texto->departamento if they exist
                    if 'epigrafe' in departamento:
                        epigrafes = departamento['epigrafe']
                        if not isinstance(epigrafes, list):
                            epigrafes = [epigrafes]
                            
                        for epigrafe in epigrafes:
                            if not isinstance(epigrafe, dict):
                                continue
                                
                            epigrafe_nombre = epigrafe.get('nombre', '')
                            
                            # Process items
                            if 'item' in epigrafe:
                                items = epigrafe['item']
                                if not isinstance(items, list):
                                    items = [items]
                                
                                for item in items:
                                    if isinstance(item, dict):
                                        # Process this item
                                        process_item(item, all_items, metadatos, diario_num, sumario_diario,
                                                  seccion_codigo, seccion_nombre, depto_codigo, depto_nombre, epigrafe_nombre)
            
            # Process each department
            if 'departamento' in seccion:
                departamentos = seccion['departamento']
                if not isinstance(departamentos, list):
                    departamentos = [departamentos] # Convert single department to list

                for departamento in departamentos:
                    if not isinstance(departamento, dict):
                        continue
                        
                    depto_codigo = departamento.get('codigo', '')
                    depto_nombre = departamento.get('nombre', '')
                    
                    # Handle the special case where 'texto' contains 'item' directly
                    if 'texto' in departamento and isinstance(departamento['texto'], dict) and 'item' in departamento['texto']:
                        items = departamento['texto']['item']
                        if not isinstance(items, list):
                            items = [items]  # Convert single item to list
                        
                        for item in items:
                            if isinstance(item, dict):
                                # Process this item
                                process_item(item, all_items, metadatos, diario_num, sumario_diario,
                                          seccion_codigo, seccion_nombre, depto_codigo, depto_nombre, 'Texto')
                    
                    # Process epigrafes if they exist
                    if 'epigrafe' in departamento:
                        epigrafes = departamento['epigrafe']
                        if not isinstance(epigrafes, list):
                            epigrafes = [epigrafes]
                            
                        for epigrafe in epigrafes:
                            if not isinstance(epigrafe, dict):
                                continue
                                
                            epigrafe_nombre = epigrafe.get('nombre', '')
                            
                            # Process items in the epigrafe
                            if 'item' in epigrafe:
                                items = epigrafe['item']
                                if not isinstance(items, list):
                                    items = [items]  # Convert single item to list
                                
                                for item in items:
                                    if isinstance(item, dict):
                                        # Process this item
                                        process_item(item, all_items, metadatos, diario_num, sumario_diario,
                                                  seccion_codigo, seccion_nombre, depto_codigo, depto_nombre, epigrafe_nombre)
                    
                    # Process items directly in the department if they exist
                    if 'item' in departamento:
                        items = departamento['item']
                        if not isinstance(items, list):
                            items = [items]  # Convert single item to list
                        
                        for item in items:
                            if isinstance(item, dict):
                                # Process this item
                                process_item(item, all_items, metadatos, diario_num, sumario_diario,
                                          seccion_codigo, seccion_nombre, depto_codigo, depto_nombre, '')
    
    # Create DataFrame from flattened list
    return DataFrame(all_items)


def process_item(item, all_items, metadatos, diario_num, sumario_diario, seccion_codigo, seccion_nombre, depto_codigo, depto_nombre, epigrafe_nombre):
    """
    Helper function to process an individual item and add it to the all_items list
    """
    # Safe extraction of url_pdf
    url_pdf_text = ''
    if 'url_pdf' in item:
        url_pdf = item['url_pdf']
        if isinstance(url_pdf, dict):
            url_pdf_text = url_pdf.get('texto', '')
        elif isinstance(url_pdf, str):
            url_pdf_text = url_pdf

    # Get sumario_url_pdf safely
    sumario_url_pdf = ''
    if sumario_diario and 'url_pdf' in sumario_diario:
        if isinstance(sumario_diario['url_pdf'], dict):
            sumario_url_pdf = sumario_diario['url_pdf'].get('texto', '')
        elif isinstance(sumario_diario['url_pdf'], str):
            sumario_url_pdf = sumario_diario['url_pdf']

    item_data = {
        'fecha_publicacion': metadatos.get('fecha_publicacion', ''),
        'publicacion': metadatos.get('publicacion', ''),
        'diario_numero': diario_num,
        'sumario_id': sumario_diario.get('identificador', ''),
        'sumario_url_pdf': sumario_url_pdf,
        'seccion_codigo': seccion_codigo,
        'seccion_nombre': seccion_nombre,
        'departamento_codigo': depto_codigo,
        'departamento_nombre': depto_nombre,
        'epigrafe_nombre': epigrafe_nombre,
        'item_id': item.get('identificador', ''),
        'item_titulo': item.get('titulo', ''),
        'item_url_pdf': url_pdf_text,
        'item_url_html': item.get('url_html', ''),
        'item_url_xml': item.get('url_xml', '')
    }
    all_items.append(item_data)


def lambda_handler(event, context):
    """
    AWS Lambda function that processes the JSON BOE data from S3,
    flattens it, and stores it as a CSV file in another S3 location.
    
    Args:
        event: AWS Lambda event object with the S3 bucket and key information
        context: AWS Lambda context object
        
    Returns:
        dict: Response containing status and information about the processed data
    """
    try:
        # Get parameters from event
        s3_bucket = event.get('s3_bucket', os.environ.get('S3_BUCKET_NAME', 'boe-facil'))
        s3_key = event.get('s3_key')
        date = event.get('date')
        
        # Derive date from S3 key if not provided
        if not date and s3_key:
            # Extract date from the filename (assuming format like "json/boe_data_20240101.json")
            filename = os.path.basename(s3_key)
            date = filename.split('_')[-1].split('.')[0]
        
        # Check if required parameters are provided
        if not s3_key:
            raise ValueError("S3 key not provided in the event")
            
        # Get environment variables
        csv_folder = os.environ.get('CSV_FOLDER', 'csv')
        
        # Create S3 client
        s3_client = boto3.client('s3')
        
        # Get the JSON file from S3
        response = s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
        json_data = json.loads(response['Body'].read().decode('utf-8'))
        
        # Flatten the JSON data
        df = flatten_boe_data(json_data)
        
        # Convert DataFrame to CSV
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        
        # Define the output S3 key
        output_s3_key = f"{csv_folder}/boe_data_{date}.csv"
        
        # Upload the CSV data to S3
        s3_client.put_object(
            Bucket=s3_bucket,
            Key=output_s3_key,
            Body=csv_buffer.getvalue(),
            ContentType='text/csv'
        )
        
        print(f"Flattened BOE data for {date} uploaded to s3://{s3_bucket}/{output_s3_key}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'BOE data successfully flattened and stored in S3',
                'date': date,
                's3_bucket': s3_bucket,
                'input_s3_key': s3_key,
                'output_s3_key': output_s3_key,
                'record_count': len(df)
            })
        }
        
    except Exception as e:
        error_message = f"Error flattening BOE data: {str(e)}"
        print(error_message)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': error_message,
                'input_s3_key': event.get('s3_key', 'unknown')
            })
        }