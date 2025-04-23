# chunking_strategy.md

## Chunking Strategy for BOE XML Documents

This document provides a clear and detailed strategy to split ("chunk") the XML documents downloaded from the BOE, using both their internal structure and the metadata from the associated CSV file. The goal is for each chunk to have semantic meaning and to facilitate further processing, analysis, or embedding.

---

## 1. General Principles

- **Semantic chunks:** Each chunk should contain a coherent unit of meaning (e.g., a resolution, a list, a table, a section).
- **Reasonable size:** Avoid excessively large chunks. If a block exceeds 1000 words, split it into smaller parts.
- **Automation:** Use CSV metadata (`boe_data_YYYYMMDD.csv`) to identify the type and subtype of each document and apply the appropriate strategy.
- **Consistency:** Use the same chunking logic for documents of the same type.

---

## 2. Identifying Types and Subtypes

Document type identification is primarily based on the following CSV columns:

- `seccion_codigo` and `seccion_nombre`
- `epigrafe_nombre`
- `departamento_nombre`
- `item_id` (matches the XML filename)

From these fields, the following main types and subtypes are distinguished:

| Section/Epigraph            | Subtype/Example                   |
|----------------------------|-----------------------------------|
| 2A Appointments            | Appointments, situations           |
| 2B Competitions/Exams      | Admission lists, tribunals         |
| 3 Universities             | Resolutions with tables/annexes    |
| 5A Public Procurement      | Tenders, contracts                 |
| 5B Other Official Notices  | Official notices, tables           |
| 5C Private Notices         | Brief notices                      |

---

## 3. Chunking Rules by Type

### 3.1. Appointments, Brief Resolutions, and Decisions (2A)

- **Identification:** `seccion_codigo = 2A`, `epigrafe_nombre = Nombramientos`
- **Structure:** Few paragraphs, no tables or lists.
- **Chunking:**  
  - Single chunk per document.
  - Optional: one chunk per paragraph if more granularity is needed.

---

### 3.2. Competitions, Exams, Admission/Exclusion Lists, Tribunals (2B)

- **Identification:** `seccion_codigo = 2B`, epigraphs like "Admitidos", "Tribunales".
- **Structure:** Introductory paragraphs, lists/tables of people, annexes.
- **Chunking:**  
  - One chunk for the introduction.
  - One chunk for each list or table (admitted, excluded, tribunals, etc.).
  - One chunk for each annex or clearly separated section.

---

### 3.3. University Resolutions, Study Plans, Decisions with Tables (3)

- **Identification:** `seccion_codigo = 3`, `departamento_nombre = Universidades`
- **Structure:** Paragraphs and extensive tables (study plans, subjects).
- **Chunking:**  
  - One chunk for the introduction.
  - One chunk for each table (or by row blocks if very large).
  - One chunk for conclusions or final decisions.

---

### 3.4. Tenders and Public Procurement (5A)

- **Identification:** `seccion_codigo = 5A`
- **Structure:** Document structured in `<dl>`, with many sections and subsections.
- **Chunking:**  
  - One chunk for each main `<dl>` section (e.g., "1. Contracting Authority", "2. Object of the Contract", etc.).
  - If a section is very long, split into additional chunks by subsection.

---

### 3.5. Other Official Notices (5B)

- **Identification:** `seccion_codigo = 5B`
- **Structure:** Explanatory paragraphs, tables of affected parties, values, dates, etc.
- **Chunking:**  
  - One chunk for each block of explanatory paragraphs.
  - One chunk for each table or logical group of rows (e.g., by affected party/lot).
  - One chunk for annexes if they exist.

---

### 3.6. Private Notices (5C)

- **Identification:** `seccion_codigo = 5C`
- **Structure:** Brief documents, only paragraphs, no complex lists or tables.
- **Chunking:**  
  - Single chunk per document.

---

### 3.7. Special Cases (Annexes, Lists, Mixed Documents)

- **Identification:** Any section with annexes, long lists, or mixed documents.
- **Structure:** Mix of paragraphs, lists, tables, annexes.
- **Chunking:**  
  - One chunk for each logical block: introduction, each list, each table, each annex, each numbered section.
  - If any part exceeds 1000 words, split into smaller chunks.

---

## 4. Example of Automatic Mapping

Below is an example of how to map a document to its chunking strategy using the CSV metadata:

```python
def get_chunking_strategy(row):
    if row['seccion_codigo'] == '2A' and row['epigrafe_nombre'] == 'Nombramientos':
        return 'document'
    elif row['seccion_codigo'] == '2B':
        return 'intro_and_each_list'
    elif row['seccion_codigo'] == '3' and row['departamento_nombre'] == 'Universidades':
        return 'intro_and_each_table'
    elif row['seccion_codigo'] == '5A':
        return 'each_dl_section'
    elif row['seccion_codigo'] == '5B':
        return 'blocks_and_tables'
    elif row['seccion_codigo'] == '5C':
        return 'document'
    else:
        return 'by_logical_blocks'
```

---

## 5. Technical Considerations

- **Data joining:** For each XML, find its corresponding row in the CSV using `item_id`.
- **XML processing:** Use libraries like `xml.etree.ElementTree` or `lxml` to identify sections, tables, and lists.
- **Granularity:** Adjust chunk size according to length and logical structure.
- **Metadata:** Save relevant metadata (title, section, epigraph, etc.) with each chunk for traceability.

---

## 6. Visual Summary

| Section/Epigraph         | Recommended Chunking                                    |
|-------------------------|---------------------------------------------------------|
| 2A Appointments         | 1 chunk per document (or per paragraph if desired)       |
| 2B Competitions/Exams   | 1 chunk per introduction/list/annex                     |
| 3 Universities          | 1 chunk per intro, 1 per table, 1 per conclusion         |
| 5A Public Procurement   | 1 chunk per main `<dl>` section                          |
| 5B Other notices        | 1 chunk per logical block/tables/annexes                 |
| 5C Private notices      | 1 chunk per document                                     |
| Special cases           | 1 chunk per logical block (intro, list, table, annex...) |

---

## 7. Best Practices

- Manually review some examples of each type to validate segmentation.
- Document any exception or special case found in the process.
- Keep documentation and code synchronized if the BOE structure changes.
