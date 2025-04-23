create table boe_metadatos (
    id bigserial primary key,
    fecha_publicacion text,
    diario_numero text,
    sumario_id text,
    seccion_codigo text,
    seccion_nombre text,
    departamento_codigo text,
    departamento_nombre text,
    epigrafe_nombre text,
    item_id text unique,
    item_titulo text,
    item_url_pdf text,
    item_url_xml text,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Seguridad
alter table boe_metadatos enable row level security;
create policy "Allow public read access"
  on boe_metadatos
  for select
  to public
  using (true);
