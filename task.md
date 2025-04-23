# BOE Data ETL Pipeline Project

Este documento describe la estructura y el flujo de trabajo de un pipeline ETL para el BOE. A continuación, se listan las tareas principales del proyecto. Marca las tareas completadas con [x] y las pendientes con [ ].

## Lista de Tareas

### Task 1: Set Up Project Environment
- [x] Inicializar estructura del proyecto y dependencias.
  - [x] Crear entorno virtual Python (`python -m venv venv`).
  - [x] Instalar librerías requeridas (`pip install requests pandas lxml supabase-py`).
  - [ ] Configurar variables de entorno para Supabase en `.env`.
  - [x] Crear estructura de directorios y archivos principales.

### Task 2: Implement API Data Extraction
- [x] Modificar `get_boe.py` para extraer datos JSON de la API BOE de forma robusta.
  - [x] Manejar errores de API y reintentos.
  - [x] Validar respuesta JSON.
  - [x] Guardar JSON crudo en `output_json/`.

### Task 3: Flatten JSON Data
- [x] Actualizar `process_boe.py` para aplanar la estructura JSON.
  - [x] Extraer campos relevantes.
  - [x] Manejar estructuras anidadas.
  - [x] Añadir logging para seguimiento.

### Task 4: Download and Parse XML
- [x] Mejorar `process_item` para descargar y parsear XML.
  - [x] Descargar XML con timeout.
  - [x] Parsear `<texto>` del XML.
  - [x] Manejar errores y guardar texto en `output_txt/`.

### Task 5: Chunk Text Content
- [ ] Implementar lógica de chunking en `process_boe.py`.
  - [ ] Dividir texto en chunks.
  - [ ] Asignar IDs únicos a cada chunk.
  - [ ] Guardar chunks en lista de diccionarios.
  - [ ] Añadir chunks al diccionario de cada ítem.

### Task 6: Set Up Supabase Database
- [ ] Configurar Supabase y definir el esquema.
  - [ ] Crear proyecto y obtener credenciales.
  - [ ] Definir tablas `boe_items` y `boe_text_chunks`.
  - [ ] Probar el esquema con datos de ejemplo.

### Task 7: Implement Database Storage
- [ ] Añadir lógica en `get_boe.py` para almacenar en Supabase.
  - [ ] Insertar metadatos en `boe_items`.
  - [ ] Insertar chunks en `boe_text_chunks`.
  - [ ] Manejar duplicados y errores.
  - [ ] Log de inserciones y errores.

### Task 8: Generate XML Output
- [ ] Crear salida XML desde los datos procesados.
  - [ ] Función para generar XML con chunks.
  - [ ] Guardar XML en `output_xml/`.
  - [ ] Soportar UTF-8 y caracteres especiales.

### Task 9: Test the Pipeline
- [x] Validar el pipeline end-to-end con datos de ejemplo.
  - [x] Ejecutar pipeline para una fecha específica.
  - [x] Verificar salidas JSON, CSV, TXT.
  - [ ] Verificar salida XML.
  - [ ] Verificar tablas Supabase.
  - [x] Probar manejo de errores.

### Task 10: Document and Deploy
- [ ] Finalizar documentación y preparar despliegue.
  - [ ] Actualizar `README.md` con instrucciones y ejemplos.
  - [ ] Documentar esquema de Supabase.
  - [ ] Automatizar ejecución diaria (ej: AWS Lambda).
  - [ ] Configurar monitorización.

## Notas
- El pipeline descarga y parsea XML para extraer y fragmentar el texto.
- Supabase se usará como base de datos (PostgreSQL).
- El chunking y la salida XML deben estar alineados con la estructura de la base de datos.
