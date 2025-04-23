# BOE Data ETL Pipeline Project

This document describes the structure and workflow of an ETL pipeline for BOE. Below is a checklist of the main project tasks. Mark completed tasks with [x] and pending ones with [ ].

## Task List

### Task 1: Set Up Project Environment
- [x] Initialize project structure and dependencies.
  - [x] Create Python virtual environment (`python -m venv venv`).
  - [x] Install required libraries (`pip install requests pandas lxml supabase-py`).
  - [ ] Set up Supabase environment variables in `.env`.
  - [x] Create directory structure and main files.

### Task 2: Implement API Data Extraction
- [x] Modify `get_boe.py` to robustly extract JSON data from the BOE API.
  - [x] Handle API errors and retries.
  - [x] Validate JSON response.
  - [x] Save raw JSON in `output_json/`.

### Task 3: Flatten JSON Data
- [x] Update `process_boe.py` to flatten the JSON structure.
  - [x] Extract relevant fields.
  - [x] Handle nested structures.
  - [x] Add logging for tracking.

### Task 4: Download and Parse XML
- [x] Improve `process_item` to download and parse XML.
  - [x] Download XML with timeout.
  - [x] Parse `<texto>` from XML.
  - [x] Handle errors and save text in `output_txt/`.

### Task 5: Chunk Text Content
- [ ] Implement chunking logic in `process_boe.py`.
  - [ ] Split text into chunks.
  - [ ] Assign unique IDs to each chunk.
  - [ ] Store chunks in a list of dictionaries.
  - [ ] Add chunks to each item dictionary.

### Task 6: Set Up Supabase Database
- [ ] Set up Supabase and define schema.
  - [ ] Create project and obtain credentials.
  - [ ] Define `boe_items` and `boe_text_chunks` tables.
  - [ ] Test schema with sample data.

### Task 7: Implement Database Storage
- [ ] Add logic in `get_boe.py` to store in Supabase.
  - [ ] Insert metadata into `boe_items`.
  - [ ] Insert chunks into `boe_text_chunks`.
  - [ ] Handle duplicates and errors.
  - [ ] Log inserts and errors.

### Task 8: Generate XML Output
- [ ] Create XML output from processed data.
  - [ ] Function to generate XML with chunks.
  - [ ] Save XML in `output_xml/`.
  - [ ] Support UTF-8 and special characters.

### Task 9: Test the Pipeline
- [x] Validate the end-to-end pipeline with sample data.
  - [x] Run pipeline for a specific date.
  - [x] Verify JSON, CSV, TXT outputs.
  - [ ] Verify XML output.
  - [ ] Verify Supabase tables.
  - [x] Test error handling.

### Task 10: Document and Deploy
- [ ] Finalize documentation and prepare deployment.
  - [ ] Update `README.md` with instructions and examples.
  - [ ] Document Supabase schema.
  - [ ] Automate daily execution (e.g., AWS Lambda).
  - [ ] Set up monitoring.

## Notes
- The pipeline downloads and parses XML to extract and chunk text.
- Supabase will be used as the database (PostgreSQL).
- Chunking and XML output should be aligned with the database structure.
