-- Agregar columna para fecha de último login
ALTER TABLE encuestas_oltp.usuario_admin
ADD COLUMN fecha_ultimo_login TIMESTAMP WITHOUT TIME ZONE NULL;

-- Agregar columna para estado activo/inactivo (Por defecto TRUE)
ALTER TABLE encuestas_oltp.usuario_admin
ADD COLUMN activo BOOLEAN NOT NULL DEFAULT TRUE;

-- Agregar columna para obligar cambio de clave (Por defecto FALSE)
ALTER TABLE encuestas_oltp.usuario_admin
ADD COLUMN debe_cambiar_clave BOOLEAN NOT NULL DEFAULT FALSE;
