# 2.0 Estrategia Universal de Chunking BOE (2025)

## Resumen del enfoque
Se va simplicar la estrategia de chunking, se adopta una estrategia de chunking universal para todos los documentos del BOE, salvo excepciones justificadas. Esto simplifica el código, mejora la coherencia y facilita el mantenimiento.

---

## Lógica universal

- **Todos los documentos** se procesan recorriendo en orden todos los bloques relevantes del XML (`<p>`, `<table>`, `<ul>`, `<ol>`, `<dl>`, etc.).
- Cada bloque se convierte a formato Markdown.
- Los bloques se van acumulando en un chunk hasta alcanzar un máximo de tokens (`max_tokens`, por defecto 500).
- Si se supera el límite, se guarda el chunk y se comienza uno nuevo.
- Cada chunk termina siempre en el final de un bloque lógico, nunca parte un párrafo, tabla o lista por la mitad.
- Los archivos se guardan en la carpeta `chunks_universal`.

---

## Excepción: Contratación pública (Sección 5A)

- **Motivo:** La estructura legal de estos documentos se basa en bloques `<dl>`, cada uno representando un apartado independiente.
- **Chunking especial:**  
  - Se genera un chunk Markdown por cada bloque `<dl>`.
  - Cada chunk contiene todos los `<dt>` y `<dd>` de ese bloque, respetando la estructura legal.
  - Los archivos se guardan en la carpeta `chunks_5A`.

---

## Ventajas del nuevo enfoque

- **Simplicidad:** Un único método cubre la gran mayoría de los casos.
- **Robustez:** Menos código, menos errores, más fácil de mantener.
- **Contexto:** Cada chunk mantiene la máxima coherencia semántica posible.
- **Flexibilidad:** Si surge un nuevo caso especial, solo hay que añadir una excepción puntual.

---

## Ejemplo de pipeline

1. Procesar todos los documentos con la función universal.
2. Si el documento es de contratación pública (5A), aplicar la excepción y procesar por `<dl>`.
3. En el futuro, añadir nuevas excepciones solo si la estructura lo requiere.
