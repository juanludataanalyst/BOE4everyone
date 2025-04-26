-- Habilita la extensión pgvector (solo una vez)
create extension if not exists vector;

create table boe_chunks (
    id bigserial primary key,
    item_id text not null,                   -- Referencia al documento BOE
    chunk_number integer not null,           -- Índice del chunk en el documento
    chunk_id text not null,                  -- item_id + '_' + chunk_number (único por chunk)
    chunk_text text not null,                -- Texto del chunk
    embedding vector(384) not null,         -- Ajusta la dimensión según tu modelo (ej: OpenAI 1536)
    metadata jsonb not null default '{}'::jsonb, -- Metadatos adicionales
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    unique(item_id, chunk_number)
);

-- Índice para búsquedas vectoriales rápidas
create index on boe_chunks using ivfflat (embedding vector_cosine_ops);

-- Índice GIN sobre metadatos para filtrado eficiente
create index idx_boe_chunks_metadata on boe_chunks using gin (metadata);

-- Función para búsqueda semántica de chunks
create function match_boe_chunks (
  query_embedding vector(384),
  match_count int default 10,
  filter jsonb DEFAULT '{}'::jsonb
) returns table (
  id bigint,
  item_id text,
  chunk_number integer,
  chunk_id text,
  chunk_text text,
  embedding vector(384),
  metadata jsonb,
  similarity float
)
language plpgsql
as $$
#variable_conflict use_column
begin
  return query
  select
    id,
    item_id,
    chunk_number,
    chunk_id,
    chunk_text,
    embedding,
    metadata,
    1 - (boe_chunks.embedding <=> query_embedding) as similarity
  from boe_chunks
  where metadata @> filter
  order by boe_chunks.embedding <=> query_embedding
  limit match_count;
end;
$$;

-- Seguridad
alter table boe_chunks enable row level security;
create policy "Allow public read access"
  on boe_chunks
  for select
  to public
  using (true);
