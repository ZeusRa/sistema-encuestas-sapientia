-- update_schema_2.sql
-- Add missing columns to encuestas_oltp.regla_asignacion

ALTER TABLE encuestas_oltp.regla_asignacion ADD COLUMN IF NOT EXISTS filtros_json JSONB;
