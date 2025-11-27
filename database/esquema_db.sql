-- =============================================================================
-- Script de Inicialización de Base de Datos - Sistema de Encuestas
-- =============================================================================

-- 1. Crear Esquemas
CREATE SCHEMA IF NOT EXISTS encuestas_oltp;
CREATE SCHEMA IF NOT EXISTS encuestas_olap;

-- =============================================================================
-- ESQUEMA OLTP (Transaccional)
-- =============================================================================

-- Tipos ENUM
CREATE TYPE encuestas_oltp.prioridad_encuesta AS ENUM ('obligatoria', 'opcional', 'evaluacion_docente');
CREATE TYPE encuestas_oltp.accion_disparadora AS ENUM ('al_iniciar_sesion', 'al_ver_curso', 'al_inscribir_examen');
create type encuestas_oltp.estado_encuesta as enum ('borrador','publicado','en curso','finalizado');
CREATE TYPE encuestas_oltp.tipo_pregunta AS ENUM ('texto_libre', 'opcion_unica', 'opcion_multiple', 'matriz','seccion');
CREATE TYPE encuestas_oltp.estado_asignacion AS ENUM ('pendiente', 'realizada', 'cancelada');
CREATE TYPE encuestas_oltp.publico_objetivo AS ENUM ('alumnos', 'docentes', 'ambos');
-- Eliminado PROFESOR del enum de roles administrativos
CREATE TYPE encuestas_oltp.rol_admin AS ENUM ('ADMINISTRADOR', 'DIRECTIVO');

-- Tabla: Usuarios Administrativos
CREATE TABLE encuestas_oltp.usuario_admin (
    id_admin SERIAL PRIMARY KEY,
    nombre_usuario VARCHAR(50) NOT NULL UNIQUE,
    clave_encriptada VARCHAR(255) NOT NULL,
    rol encuestas_oltp.rol_admin NOT NULL,
    -- Eliminado id_profesor_contexto ya que no acceden por aquí
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: Encuestas
CREATE TABLE encuestas_oltp.encuesta (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    fecha_inicio TIMESTAMP NOT NULL,
    fecha_fin TIMESTAMP NOT NULL,
    prioridad encuestas_oltp.prioridad_encuesta NOT NULL,
    accion_disparadora encuestas_oltp.accion_disparadora NOT NULL,
    activo BOOLEAN DEFAULT TRUE
);

-- Tabla: Reglas de Asignación
CREATE TABLE encuestas_oltp.regla_asignacion (
    id SERIAL PRIMARY KEY,
    id_encuesta INT NOT NULL REFERENCES encuestas_oltp.encuesta(id) ON DELETE CASCADE,
    id_facultad INT, 
    id_carrera INT,  
    id_asignatura INT, 
    publico_objetivo encuestas_oltp.publico_objetivo NOT NULL
);

-- Tabla: Preguntas
CREATE TABLE encuestas_oltp.pregunta (
    id SERIAL PRIMARY KEY,
    id_encuesta INT NOT NULL REFERENCES encuestas_oltp.encuesta(id) ON DELETE CASCADE,
    texto_pregunta TEXT NOT NULL,
    orden INT NOT NULL,
    tipo encuestas_oltp.tipo_pregunta NOT NULL,
    configuracion_json JSONB, 
    activo BOOLEAN DEFAULT TRUE
);

-- Tabla: Opciones de Respuesta
CREATE TABLE encuestas_oltp.opcion_respuesta (
    id SERIAL PRIMARY KEY,
    id_pregunta INT NOT NULL REFERENCES encuestas_oltp.pregunta(id) ON DELETE CASCADE,
    texto_opcion VARCHAR(255) NOT NULL,
    orden INT NOT NULL
);

-- Tabla: Asignaciones de Usuario
CREATE TABLE encuestas_oltp.asignacion_usuario (
    id SERIAL PRIMARY KEY,
    id_usuario INT NOT NULL, -- ID externo (Alumno/Profesor)
    id_encuesta INT NOT NULL REFERENCES encuestas_oltp.encuesta(id),
    estado encuestas_oltp.estado_asignacion DEFAULT 'pendiente',
    fecha_asignacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_realizacion TIMESTAMP,
    UNIQUE(id_usuario, id_encuesta)
);

-- Tabla: Borrador de Respuestas
CREATE TABLE encuestas_oltp.respuesta_borrador (
    id SERIAL PRIMARY KEY,
    id_asignacion INT NOT NULL UNIQUE REFERENCES encuestas_oltp.asignacion_usuario(id) ON DELETE CASCADE,
    respuestas_json JSONB NOT NULL,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: Transacciones de Encuesta (Anónimo)
CREATE TABLE encuestas_oltp.transaccion_encuesta (
    id_transaccion SERIAL PRIMARY KEY,
    id_encuesta INT NOT NULL REFERENCES encuestas_oltp.encuesta(id),
    fecha_finalizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadatos_contexto JSONB NOT NULL,
    procesado_etl BOOLEAN DEFAULT FALSE
);

-- Tabla: Respuestas Detalladas (Anónimo)
CREATE TABLE encuestas_oltp.respuesta (
    id_respuesta SERIAL PRIMARY KEY,
    id_transaccion INT NOT NULL REFERENCES encuestas_oltp.transaccion_encuesta(id_transaccion) ON DELETE CASCADE,
    id_pregunta INT NOT NULL REFERENCES encuestas_oltp.pregunta(id),
    valor_respuesta TEXT,
    id_opcion INT REFERENCES encuestas_oltp.opcion_respuesta(id)
);

-- Índices
CREATE INDEX idx_asignacion_usuario_estado ON encuestas_oltp.asignacion_usuario(id_usuario, estado);
CREATE INDEX idx_encuesta_disparador ON encuestas_oltp.encuesta(accion_disparadora);

-- =============================================================================
-- ESQUEMA OLAP (Analítico)
-- =============================================================================

CREATE TABLE encuestas_olap.dim_tiempo (
    id_dim_tiempo SERIAL PRIMARY KEY,
    fecha DATE UNIQUE NOT NULL,
    anho INT NOT NULL, 
    semestre INT NOT NULL,
    mes INT NOT NULL,
    dia_semana VARCHAR(20)
);

CREATE TABLE encuestas_olap.dim_ubicacion (
    id_dim_ubicacion SERIAL PRIMARY KEY,
    nombre_facultad VARCHAR(100),
    nombre_carrera VARCHAR(100),
    nombre_campus VARCHAR(100),
    CONSTRAINT uniq_ubicacion UNIQUE (nombre_facultad, nombre_carrera, nombre_campus)
);

CREATE TABLE encuestas_olap.dim_contexto_academico (
    id_dim_contexto SERIAL PRIMARY KEY,
    nombre_profesor VARCHAR(100),
    nombre_asignatura VARCHAR(100),
    semestre_curso INT,
    CONSTRAINT uniq_contexto UNIQUE (nombre_profesor, nombre_asignatura)
);

CREATE TABLE encuestas_olap.dim_pregunta (
    id_dim_pregunta SERIAL PRIMARY KEY,
    texto_pregunta TEXT NOT NULL,
    nombre_encuesta VARCHAR(100) NOT NULL,
    tipo_pregunta VARCHAR(50)
);

CREATE TABLE encuestas_olap.hechos_respuestas (
    id_hecho BIGSERIAL PRIMARY KEY,
    id_transaccion_origen INT,
    
    -- Claves Foráneas
    id_dim_tiempo INT REFERENCES encuestas_olap.dim_tiempo(id_dim_tiempo),
    id_dim_ubicacion INT REFERENCES encuestas_olap.dim_ubicacion(id_dim_ubicacion),
    id_dim_contexto INT REFERENCES encuestas_olap.dim_contexto_academico(id_dim_contexto),
    id_dim_pregunta INT REFERENCES encuestas_olap.dim_pregunta(id_dim_pregunta),
    
    -- Métricas
    respuesta_numerica NUMERIC,
    respuesta_texto TEXT,
    conteo INT DEFAULT 1
);