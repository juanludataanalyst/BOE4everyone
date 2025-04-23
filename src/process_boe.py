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
