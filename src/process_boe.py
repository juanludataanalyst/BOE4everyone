import requests
from xml.etree import ElementTree as ET
import time


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
    
    return all_items

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
            pdf_kbytes = url_pdf.get('szKBytes', 0)
        elif isinstance(url_pdf, str):
            url_pdf_text = url_pdf
            pdf_kbytes = 0  # Default to 0 if not provided

    # Get sumario_url_pdf safely
    sumario_url_pdf = ''
    if sumario_diario and 'url_pdf' in sumario_diario:
        if isinstance(sumario_diario['url_pdf'], dict):
            sumario_url_pdf = sumario_diario['url_pdf'].get('texto', '')
        elif isinstance(sumario_diario['url_pdf'], str):
            sumario_url_pdf = sumario_diario['url_pdf']
    
    # Get item URL XML
    item_url_xml = item.get('url_xml', '')
    
    # Get texto from XML if available
    item_texto = ''
    if item_url_xml:
        try:

            # Add sleep time to avoid rate limiting
            time.sleep(0.25)  # Sleep for 1 second between requests
            
            # Fetch XML data from url with retry mechanism
            max_retries = 5
            retry_delay = 2  # seconds
            
            for retry in range(max_retries):
                try:
                    response = requests.get(item_url_xml, timeout=30)
                    if response.status_code == 200:
                        break
                    elif response.status_code == 429:  # Too Many Requests
                        # Exponential backoff
                        sleep_time = retry_delay * (2 ** retry)
                        print(f"Rate limit reached. Waiting {sleep_time} seconds before retrying...")
                        time.sleep(sleep_time)
                    else:
                        print(f"Request failed with status code {response.status_code}, retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                except requests.exceptions.RequestException as e:
                    print(f"Request error: {str(e)}, retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    
            if response.status_code == 200:
                # Parse XML
                tree = ET.fromstring(response.content)
                # Find texto element (XPath: /documento/texto)
                texto_element = tree.find('.//texto')
                if texto_element is not None:
                    # Convert all child elements to text
                    texto_content = []
                    for elem in texto_element.iter():
                        if elem.tag != 'texto' and elem.text:  # Skip the texto tag itself
                            texto_content.append(elem.text.strip())
                    # Join all text parts with spaces instead of newlines
                    raw_texto = ' '.join([t for t in texto_content if t])
                    # Replace pipe characters with a safe alternative for CSV compatibility
                    item_texto = raw_texto.replace('|', '&#124;')
            else:
                print(f"Failed to fetch XML after {max_retries} retries: {item_url_xml}")
        except Exception as e:
            # Log error but continue processing
            print(f"Error fetching XML from {item_url_xml}: {str(e)}")

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
        'item_url_xml': item_url_xml,
        'texto': item_texto,  # Add the extracted texto to the item data
        'szKBytes': pdf_kbytes,
    }
    all_items.append(item_data)
