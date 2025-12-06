-- update_schema.sql
-- Add missing columns to encuestas_oltp.usuario_admin

ALTER TABLE encuestas_oltp.usuario_admin ADD COLUMN IF NOT EXISTS fecha_ultimo_login TIMESTAMP WITH TIME ZONE;
ALTER TABLE encuestas_oltp.usuario_admin ADD COLUMN IF NOT EXISTS activo BOOLEAN DEFAULT TRUE NOT NULL;
ALTER TABLE encuestas_oltp.usuario_admin ADD COLUMN IF NOT EXISTS debe_cambiar_clave BOOLEAN DEFAULT FALSE NOT NULL;
