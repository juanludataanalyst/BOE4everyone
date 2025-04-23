create table boe_metadatos (
    id bigserial primary key,
    fecha_publicacion date,
    diario_numero integer,
    sumario_id text,
    seccion_codigo text,
    seccion_nombre text,
    departamento_codigo integer,
    departamento_nombre text,
    epigrafe_nombre text,
    item_id text unique,
    item_titulo text,
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
create policy "Allow public insert access"
  on boe_metadatos
  for insert
  to public
  with check (true);
create policy "Allow public update access"
  on boe_metadatos
  for update
  to public
  using (true);
