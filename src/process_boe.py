import requests
from xml.etree import ElementTree as ET
import time

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


def process_item(item, all_items, metadatos, diario_num, sumario_diario, seccion_codigo, seccion_nombre, depto_codigo, depto_nombre, epigrafe_nombre):
    item_url_xml = item.get('url_xml', '')
    print(f"📥 Descargando XML: {item_url_xml}")
    
    item_texto = ''
    if item_url_xml:
        try:
            time.sleep(0.25)
            max_retries = 5
            retry_delay = 2
            
            for retry in range(max_retries):
                try:
                    response = requests.get(item_url_xml, timeout=30)
                    if response.status_code == 200:
                        break
                    elif response.status_code == 429:
                        sleep_time = retry_delay * (2 ** retry)
                        print(f"⏳ Rate limit alcanzado. Esperando {sleep_time}s antes de reintentar...")
                        time.sleep(sleep_time)
                    else:
                        print(f"⚠️ Status {response.status_code}. Reintentando en {retry_delay}s...")
                        time.sleep(retry_delay)
                except requests.exceptions.RequestException as e:
                    print(f"❌ Error de red: {str(e)}")
                    time.sleep(retry_delay)
            
            if response.status_code == 200:
                tree = ET.fromstring(response.content)
                texto_element = tree.find('.//texto')
                if texto_element is not None:
                    texto_content = []
                    for elem in texto_element.iter():
                        if elem.tag != 'texto' and elem.text:
                            texto_content.append(elem.text.strip())
                    item_texto = ' '.join(texto_content).replace('|', '&#124;')
            else:
                print(f"❌ No se pudo descargar el XML tras {max_retries} intentos: {item_url_xml}")
        except Exception as e:
            print(f"🚨 Excepción general en process_item(): {str(e)}")
    
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
        'item_url_pdf': item.get('url_pdf', ''),
        'item_url_html': item.get('url_html', ''),
        'item_url_xml': item_url_xml,
        'texto': item_texto,
        'szKBytes': item.get('szKBytes', 0),
    }

    print(f"✅ Item añadido: {item_data['item_titulo'][:60]}...")
    all_items.append(item_data)
