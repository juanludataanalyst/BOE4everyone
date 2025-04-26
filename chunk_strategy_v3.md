# 2.0 Estrategia Universal de Chunking BOE (2025)

## Resumen del enfoque
Se va a simplificar la estrategia de chunking: **se adopta una estrategia universal para todos los documentos del BOE**. Esto simplifica el código, mejora la coherencia y facilita el mantenimiento.

---

## Estrategia actual activa (Abril 2025)

- **Todos los documentos** se procesan recorriendo en orden todos los bloques relevantes del XML (`<p>`, `<table>`, `<ul>`, `<ol>`, `<dl>`, etc.).
- Cada bloque se convierte a formato Markdown.
- Los bloques se van acumulando en un chunk hasta alcanzar un máximo de tokens (`max_tokens`, actualmente 1000).
- Si se supera el límite, se guarda el chunk y se comienza uno nuevo.
- Cada chunk termina siempre en el final de un bloque lógico, nunca parte un párrafo, tabla o lista por la mitad.
- Los archivos se guardan en la carpeta `chunks_universal`.

### Excepciones
- **Actualmente NO hay excepciones activas.** Todos los documentos, incluidos los de contratación pública (5A), se procesan universalmente.
- Si en el futuro se detecta que un tipo de documento requiere chunking especial (por ejemplo, por bloques `<dl>` en 5A), solo hay que descomentar la excepción en el pipeline y estará listo para funcionar.

---

## Ventajas del enfoque universal

- **Simplicidad:** Un único método cubre todos los casos.
- **Robustez:** Menos código, menos errores, más fácil de mantener.
- **Contexto:** Cada chunk mantiene la máxima coherencia semántica posible.
- **Flexibilidad:** Si surge un nuevo caso especial, solo hay que añadir una excepción puntual.

---

## Ejemplo de pipeline

1. Procesar todos los documentos con la función universal.
2. (Opcional futuro) Si el documento requiere chunking especial, aplicar la excepción correspondiente.

---

**Última actualización:** Abril 2025