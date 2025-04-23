# ETL Workflow for BOE Data Processing

This document describes the methodology of the ETL (Extract, Transform, Load) pipeline for processing data from the Boletín Oficial del Estado (BOE). It details the approach to extraction, transformation, and loading into a Supabase (PostgreSQL) database, specifies which columns are eliminated and why, and describes the structure of the XML output. The `texto` field is downloaded later from `item_url_xml` in a separate process.

## Methodology
The ETL pipeline follows a structured methodology prioritizing reliability, scalability, and data integrity. The process is divided into three phases: Extract, Transform, and Load, with specific steps for the BOE API data structure and deferred text extraction.

### 1. Extract Phase
- **Objective:** Retrieve raw JSON data from the BOE API for a specific date.
- **Source:** BOE API (`https://www.boe.es/datosabiertos/api/boe/sumario/{date}`), where `date` is YYYYMMDD.
- **Process:**
  - Use Python's `requests` library to fetch JSON, with retry logic for HTTP 429 and network errors (max 5 retries, exponential backoff).
  - Validate the JSON response (`data` and `sumario`).
  - Save the raw JSON to `output_json/boe_data_{date}.json` (or S3).
- **Error Handling:**
  - Log API failures and skip processing if response is invalid.
  - Alert on repeated failures for monitoring.

### 2. Transform Phase
- **Objective:** Convert JSON into a structured format, prepare metadata, and generate XML, deferring `texto` extraction.
- **Steps:**
  - **Flatten JSON:** Process the nested structure into a flat list of dictionaries with essential metadata.
  - **Clean Data:** Remove unnecessary columns, normalize data (UTF-8), validate values.
  - **Generate XML:** Create an XML file with metadata only, excluding `texto` (to be fetched later).
- **Deferred Text Processing:**
  - The `texto` field is not downloaded or parsed in the initial ETL. A separate script will download XMLs from `item_url_xml`, extract `<texto>`, and chunk the content for storage.
- **Output:**
  - Flattened dataset with metadata only.
  - XML file (`output_xml/boe_data_{date}.xml`) with metadata only.
  - No text files or chunks are generated in this phase.

### 3. Load Phase
- **Objective:** Store the transformed metadata in Supabase for persistence and analysis.
- **Database:** Supabase (PostgreSQL).
- **Schema:**
  - **Table `boe_items`:** Stores metadata for each BOE item (e.g., item_id, fecha_publicacion, item_titulo). PK: id. Unique: item_id.
  - **Table `boe_text_chunks` (later):** Will store text chunks linked by item_id. PK: id. Unique: chunk_id (`{item_id}_chunk_{index}`).
- **Process:**
  - Use `supabase-py` to insert metadata into `boe_items`.
  - Handle duplicates (item_id) by skipping or updating.
  - Log rows inserted and errors.
  - `boe_text_chunks` will be populated after text processing.
- **Error Handling:**
  - Use transactions for consistency.
  - Retry failed inserts (max 3 attempts).

## Eliminated Columns
Columns that are redundant, irrelevant, or unnecessary for the BOE4Everyone project's goals (chat querying) are eliminated:

| Column               | Reason for Elimination                                                             |
|----------------------|-----------------------------------------------------------------------------------|
| szKBytes             | Redundant/inconsistent; file size is not used.                                     |
| publicacion          | Static value ("BOE"); no analytical value.                                        |
| sumario_url_pdf      | Not needed for querying; item_url_pdf is sufficient.                               |
| item_url_html        | Redundant; PDF/XML provide sufficient access.                                      |
| texto                | Processed later, not in initial ETL.                                              |
| Unnamed/Empty        | CSV artifacts; contain no data.                                                    |
| Nested JSON Metadata | Internal API fields not used.                                                      |

**Rationale:**
- Redundancy and storage efficiency.
- Irrelevance for analysis and chat interface.
- Deferred text processing reduces initial load.

## Retained Columns
The following columns are kept as they are essential for identification, categorization, and querying:

| Column               | Description                                         | Main Use                          |
|----------------------|-----------------------------------------------------|-----------------------------------|
| fecha_publicacion    | Publication date (YYYYMMDD)                         | Temporal filtering                |
| diario_numero        | Diary number                                        | Reference to a specific BOE issue |
| sumario_id           | Summary identifier                                  | Link to daily summary             |
| seccion_codigo       | Section code                                        | Categorization                    |
| seccion_nombre       | Section name                                        | Human-readable description        |
| departamento_codigo  | Department code                                     | Organizational filtering          |
| departamento_nombre  | Department name                                     | Organizational context            |
| epigrafe_nombre      | Epigraph name                                       | Sub-category                      |
| item_id              | Item identifier                                     | Unique identification             |
| item_titulo          | Item title                                          | Content summary                   |
| item_url_pdf         | PDF URL                                             | Access to full document           |
| item_url_xml         | XML URL                                             | Source for deferred text          |

## XML Structure
The XML output represents the processed metadata, excluding `texto`, and is aligned with the database schema.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<BOE>
    <Item>
        <fecha_publicacion>20250422</fecha_publicacion>
        <diario_numero>97</diario_numero>
        <sumario_id>BOE-S-2025-97</sumario_id>
        <seccion_codigo>1</seccion_codigo>
        <seccion_nombre>I. Disposiciones generales</seccion_nombre>
        <departamento_codigo>7786</departamento_codigo>
        <departamento_nombre>PRESIDENCIA DEL GOBIERNO</departamento_nombre>
        <epigrafe_nombre>Luto nacional</epigrafe_nombre>
        <item_id>BOE-A-2025-8107</item_id>
        <item_titulo>Real Decreto 343/2025, de 21 de abril, por el que se declara luto oficial...</item_titulo>
        <item_url_pdf>https://www.boe.es/boe/dias/2025/04/22/pdfs/BOE-A-2025-8107.pdf</item_url_pdf>
        <item_url_xml>https://www.boe.es/diario_boe/xml.php?id=BOE-A-2025-8107</item_url_xml>
    </Item>
    <!-- More <Item> elements -->
</BOE>
```

**Key Features:**
- Only essential metadata, no `<texto>` or `<TextChunks>`.
- UTF-8 encoding.
- Saved in `output_xml/boe_data_{date}.xml`.

## Deferred Text Processing
- A separate script will download XMLs from `item_url_xml`, extract `<texto>`, chunk and store in `boe_text_chunks`.
- Runs scheduled or on-demand after the initial ETL.
- Chunks stored with: id, chunk_id, item_id, chunk_text, chunk_index.

## Additional Considerations
- **Scalability:** Process metadata in batches; use async HTTP for XML.
- **Integrity:** Validate unique item_id; ensure well-formed XML.
- **Monitoring:** Log metrics and set up alerts for failures.
- **Maintenance:** Document workflow and monitor BOE API for changes.

## Conclusion
This ETL workflow streamlines BOE data processing by eliminating redundant columns and deferring text handling, aligning XML and database structure for efficient querying in BOE4Everyone.
