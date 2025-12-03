--
-- PostgreSQL database dump
--

\restrict hSQaGl8JxKMbjNdxIRrCT3StUBNKlsHhU7p1hLK4c00Te9PBYISDmoHbuCoL7J6

-- Dumped from database version 16.11
-- Dumped by pg_dump version 16.11

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: encuestas_olap; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA encuestas_olap;


--
-- Name: encuestas_oltp; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA encuestas_oltp;


--
-- Name: accion_disparadora; Type: TYPE; Schema: encuestas_oltp; Owner: -
--

CREATE TYPE encuestas_oltp.accion_disparadora AS ENUM (
    'al_iniciar_sesion',
    'al_ver_curso',
    'al_inscribir_examen'
);


--
-- Name: acciondisparadora; Type: TYPE; Schema: encuestas_oltp; Owner: -
--

CREATE TYPE encuestas_oltp.acciondisparadora AS ENUM (
    'al_iniciar_sesion',
    'al_ver_curso',
    'al_inscribir_examen'
);


--
-- Name: estado_asignacion; Type: TYPE; Schema: encuestas_oltp; Owner: -
--

CREATE TYPE encuestas_oltp.estado_asignacion AS ENUM (
    'pendiente',
    'realizada',
    'cancelada'
);


--
-- Name: estado_encuesta; Type: TYPE; Schema: encuestas_oltp; Owner: -
--

CREATE TYPE encuestas_oltp.estado_encuesta AS ENUM (
    'borrador',
    'publicado',
    'en_curso',
    'finalizado'
);


--
-- Name: estadoasignacion; Type: TYPE; Schema: encuestas_oltp; Owner: -
--

CREATE TYPE encuestas_oltp.estadoasignacion AS ENUM (
    'pendiente',
    'realizada',
    'cancelada'
);


--
-- Name: estadoencuesta; Type: TYPE; Schema: encuestas_oltp; Owner: -
--

CREATE TYPE encuestas_oltp.estadoencuesta AS ENUM (
    'borrador',
    'publicado'
);


--
-- Name: prioridad_encuesta; Type: TYPE; Schema: encuestas_oltp; Owner: -
--

CREATE TYPE encuestas_oltp.prioridad_encuesta AS ENUM (
    'obligatoria',
    'opcional',
    'evaluacion_docente'
);


--
-- Name: prioridadencuesta; Type: TYPE; Schema: encuestas_oltp; Owner: -
--

CREATE TYPE encuestas_oltp.prioridadencuesta AS ENUM (
    'obligatoria',
    'opcional',
    'evaluacion_docente'
);


--
-- Name: publico_objetivo; Type: TYPE; Schema: encuestas_oltp; Owner: -
--

CREATE TYPE encuestas_oltp.publico_objetivo AS ENUM (
    'alumnos',
    'docentes',
    'ambos'
);


--
-- Name: publicoobjetivo; Type: TYPE; Schema: encuestas_oltp; Owner: -
--

CREATE TYPE encuestas_oltp.publicoobjetivo AS ENUM (
    'alumnos',
    'docentes',
    'ambos'
);


--
-- Name: rol_admin; Type: TYPE; Schema: encuestas_oltp; Owner: -
--

CREATE TYPE encuestas_oltp.rol_admin AS ENUM (
    'ADMINISTRADOR',
    'DIRECTIVO'
);


--
-- Name: roladmin; Type: TYPE; Schema: encuestas_oltp; Owner: -
--

CREATE TYPE encuestas_oltp.roladmin AS ENUM (
    'ADMINISTRADOR',
    'DIRECTIVO'
);


--
-- Name: tipo_pregunta; Type: TYPE; Schema: encuestas_oltp; Owner: -
--

CREATE TYPE encuestas_oltp.tipo_pregunta AS ENUM (
    'texto_libre',
    'opcion_unica',
    'opcion_multiple',
    'matriz',
    'seccion'
);


--
-- Name: tipopregunta; Type: TYPE; Schema: encuestas_oltp; Owner: -
--

CREATE TYPE encuestas_oltp.tipopregunta AS ENUM (
    'texto_libre',
    'opcion_unica',
    'opcion_multiple',
    'matriz'
);


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: dim_contexto_academico; Type: TABLE; Schema: encuestas_olap; Owner: -
--

CREATE TABLE encuestas_olap.dim_contexto_academico (
    id_dim_contexto integer NOT NULL,
    nombre_profesor character varying(100),
    nombre_asignatura character varying(100),
    semestre_curso integer
);


--
-- Name: dim_contexto_academico_id_dim_contexto_seq; Type: SEQUENCE; Schema: encuestas_olap; Owner: -
--

CREATE SEQUENCE encuestas_olap.dim_contexto_academico_id_dim_contexto_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dim_contexto_academico_id_dim_contexto_seq; Type: SEQUENCE OWNED BY; Schema: encuestas_olap; Owner: -
--

ALTER SEQUENCE encuestas_olap.dim_contexto_academico_id_dim_contexto_seq OWNED BY encuestas_olap.dim_contexto_academico.id_dim_contexto;


--
-- Name: dim_pregunta; Type: TABLE; Schema: encuestas_olap; Owner: -
--

CREATE TABLE encuestas_olap.dim_pregunta (
    id_dim_pregunta integer NOT NULL,
    texto_pregunta text NOT NULL,
    nombre_encuesta character varying(100) NOT NULL,
    tipo_pregunta character varying(50)
);


--
-- Name: dim_pregunta_id_dim_pregunta_seq; Type: SEQUENCE; Schema: encuestas_olap; Owner: -
--

CREATE SEQUENCE encuestas_olap.dim_pregunta_id_dim_pregunta_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dim_pregunta_id_dim_pregunta_seq; Type: SEQUENCE OWNED BY; Schema: encuestas_olap; Owner: -
--

ALTER SEQUENCE encuestas_olap.dim_pregunta_id_dim_pregunta_seq OWNED BY encuestas_olap.dim_pregunta.id_dim_pregunta;


--
-- Name: dim_tiempo; Type: TABLE; Schema: encuestas_olap; Owner: -
--

CREATE TABLE encuestas_olap.dim_tiempo (
    id_dim_tiempo integer NOT NULL,
    fecha date NOT NULL,
    anho integer NOT NULL,
    semestre integer NOT NULL,
    mes integer NOT NULL,
    dia_semana character varying(20)
);


--
-- Name: dim_tiempo_id_dim_tiempo_seq; Type: SEQUENCE; Schema: encuestas_olap; Owner: -
--

CREATE SEQUENCE encuestas_olap.dim_tiempo_id_dim_tiempo_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dim_tiempo_id_dim_tiempo_seq; Type: SEQUENCE OWNED BY; Schema: encuestas_olap; Owner: -
--

ALTER SEQUENCE encuestas_olap.dim_tiempo_id_dim_tiempo_seq OWNED BY encuestas_olap.dim_tiempo.id_dim_tiempo;


--
-- Name: dim_ubicacion; Type: TABLE; Schema: encuestas_olap; Owner: -
--

CREATE TABLE encuestas_olap.dim_ubicacion (
    id_dim_ubicacion integer NOT NULL,
    nombre_facultad character varying(100),
    nombre_carrera character varying(100),
    nombre_campus character varying(100)
);


--
-- Name: dim_ubicacion_id_dim_ubicacion_seq; Type: SEQUENCE; Schema: encuestas_olap; Owner: -
--

CREATE SEQUENCE encuestas_olap.dim_ubicacion_id_dim_ubicacion_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dim_ubicacion_id_dim_ubicacion_seq; Type: SEQUENCE OWNED BY; Schema: encuestas_olap; Owner: -
--

ALTER SEQUENCE encuestas_olap.dim_ubicacion_id_dim_ubicacion_seq OWNED BY encuestas_olap.dim_ubicacion.id_dim_ubicacion;


--
-- Name: hechos_respuestas; Type: TABLE; Schema: encuestas_olap; Owner: -
--

CREATE TABLE encuestas_olap.hechos_respuestas (
    id_hecho bigint NOT NULL,
    id_transaccion_origen integer,
    id_dim_tiempo integer,
    id_dim_ubicacion integer,
    id_dim_contexto integer,
    id_dim_pregunta integer,
    respuesta_numerica numeric,
    respuesta_texto text,
    conteo integer DEFAULT 1
);


--
-- Name: hechos_respuestas_id_hecho_seq; Type: SEQUENCE; Schema: encuestas_olap; Owner: -
--

CREATE SEQUENCE encuestas_olap.hechos_respuestas_id_hecho_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: hechos_respuestas_id_hecho_seq; Type: SEQUENCE OWNED BY; Schema: encuestas_olap; Owner: -
--

ALTER SEQUENCE encuestas_olap.hechos_respuestas_id_hecho_seq OWNED BY encuestas_olap.hechos_respuestas.id_hecho;


--
-- Name: asignacion_usuario; Type: TABLE; Schema: encuestas_oltp; Owner: -
--

CREATE TABLE encuestas_oltp.asignacion_usuario (
    id integer NOT NULL,
    id_usuario integer NOT NULL,
    id_encuesta integer NOT NULL,
    estado encuestas_oltp.estado_asignacion DEFAULT 'pendiente'::encuestas_oltp.estado_asignacion,
    fecha_asignacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    fecha_realizacion timestamp without time zone,
    id_referencia_contexto character varying(100)
);


--
-- Name: asignacion_usuario_id_seq; Type: SEQUENCE; Schema: encuestas_oltp; Owner: -
--

CREATE SEQUENCE encuestas_oltp.asignacion_usuario_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: asignacion_usuario_id_seq; Type: SEQUENCE OWNED BY; Schema: encuestas_oltp; Owner: -
--

ALTER SEQUENCE encuestas_oltp.asignacion_usuario_id_seq OWNED BY encuestas_oltp.asignacion_usuario.id;


--
-- Name: encuesta; Type: TABLE; Schema: encuestas_oltp; Owner: -
--

CREATE TABLE encuestas_oltp.encuesta (
    id integer NOT NULL,
    nombre character varying(100) NOT NULL,
    descripcion text,
    fecha_inicio timestamp without time zone NOT NULL,
    fecha_fin timestamp without time zone NOT NULL,
    prioridad encuestas_oltp.prioridad_encuesta NOT NULL,
    activo boolean DEFAULT true,
    estado encuestas_oltp.estado_encuesta DEFAULT 'borrador'::encuestas_oltp.estado_encuesta,
    acciones_disparadoras jsonb DEFAULT '[]'::jsonb,
    configuracion jsonb DEFAULT '{}'::jsonb,
    mensaje_final text,
    usuario_creacion integer NOT NULL,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    usuario_modificacion integer,
    fecha_modificacion timestamp without time zone
);


--
-- Name: encuesta_id_seq; Type: SEQUENCE; Schema: encuestas_oltp; Owner: -
--

CREATE SEQUENCE encuestas_oltp.encuesta_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: encuesta_id_seq; Type: SEQUENCE OWNED BY; Schema: encuestas_oltp; Owner: -
--

ALTER SEQUENCE encuestas_oltp.encuesta_id_seq OWNED BY encuestas_oltp.encuesta.id;


--
-- Name: opcion_respuesta; Type: TABLE; Schema: encuestas_oltp; Owner: -
--

CREATE TABLE encuestas_oltp.opcion_respuesta (
    id integer NOT NULL,
    id_pregunta integer NOT NULL,
    texto_opcion character varying(255) NOT NULL,
    orden integer NOT NULL
);


--
-- Name: opcion_respuesta_id_seq; Type: SEQUENCE; Schema: encuestas_oltp; Owner: -
--

CREATE SEQUENCE encuestas_oltp.opcion_respuesta_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: opcion_respuesta_id_seq; Type: SEQUENCE OWNED BY; Schema: encuestas_oltp; Owner: -
--

ALTER SEQUENCE encuestas_oltp.opcion_respuesta_id_seq OWNED BY encuestas_oltp.opcion_respuesta.id;


--
-- Name: permiso; Type: TABLE; Schema: encuestas_oltp; Owner: -
--

CREATE TABLE encuestas_oltp.permiso (
    id_permiso integer NOT NULL,
    codigo character varying(50) NOT NULL,
    nombre character varying(100) NOT NULL,
    descripcion text,
    categoria character varying(30) NOT NULL
);


--
-- Name: permiso_id_permiso_seq; Type: SEQUENCE; Schema: encuestas_oltp; Owner: -
--

CREATE SEQUENCE encuestas_oltp.permiso_id_permiso_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: permiso_id_permiso_seq; Type: SEQUENCE OWNED BY; Schema: encuestas_oltp; Owner: -
--

ALTER SEQUENCE encuestas_oltp.permiso_id_permiso_seq OWNED BY encuestas_oltp.permiso.id_permiso;


--
-- Name: plantilla_opcion_detalle; Type: TABLE; Schema: encuestas_oltp; Owner: -
--

CREATE TABLE encuestas_oltp.plantilla_opcion_detalle (
    id integer NOT NULL,
    id_plantilla integer NOT NULL,
    texto_opcion character varying(255) NOT NULL,
    orden integer NOT NULL
);


--
-- Name: plantilla_opcion_detalle_id_seq; Type: SEQUENCE; Schema: encuestas_oltp; Owner: -
--

CREATE SEQUENCE encuestas_oltp.plantilla_opcion_detalle_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: plantilla_opcion_detalle_id_seq; Type: SEQUENCE OWNED BY; Schema: encuestas_oltp; Owner: -
--

ALTER SEQUENCE encuestas_oltp.plantilla_opcion_detalle_id_seq OWNED BY encuestas_oltp.plantilla_opcion_detalle.id;


--
-- Name: plantilla_opciones; Type: TABLE; Schema: encuestas_oltp; Owner: -
--

CREATE TABLE encuestas_oltp.plantilla_opciones (
    id integer NOT NULL,
    nombre character varying(100) NOT NULL,
    descripcion text,
    fecha_creacion timestamp without time zone DEFAULT now()
);


--
-- Name: plantilla_opciones_id_seq; Type: SEQUENCE; Schema: encuestas_oltp; Owner: -
--

CREATE SEQUENCE encuestas_oltp.plantilla_opciones_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: plantilla_opciones_id_seq; Type: SEQUENCE OWNED BY; Schema: encuestas_oltp; Owner: -
--

ALTER SEQUENCE encuestas_oltp.plantilla_opciones_id_seq OWNED BY encuestas_oltp.plantilla_opciones.id;


--
-- Name: pregunta; Type: TABLE; Schema: encuestas_oltp; Owner: -
--

CREATE TABLE encuestas_oltp.pregunta (
    id integer NOT NULL,
    id_encuesta integer NOT NULL,
    texto_pregunta text NOT NULL,
    orden integer NOT NULL,
    tipo encuestas_oltp.tipo_pregunta NOT NULL,
    configuracion_json jsonb,
    activo boolean DEFAULT true
);


--
-- Name: pregunta_id_seq; Type: SEQUENCE; Schema: encuestas_oltp; Owner: -
--

CREATE SEQUENCE encuestas_oltp.pregunta_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: pregunta_id_seq; Type: SEQUENCE OWNED BY; Schema: encuestas_oltp; Owner: -
--

ALTER SEQUENCE encuestas_oltp.pregunta_id_seq OWNED BY encuestas_oltp.pregunta.id;


--
-- Name: regla_asignacion; Type: TABLE; Schema: encuestas_oltp; Owner: -
--

CREATE TABLE encuestas_oltp.regla_asignacion (
    id integer NOT NULL,
    id_encuesta integer NOT NULL,
    id_facultad integer,
    id_carrera integer,
    id_asignatura integer,
    publico_objetivo encuestas_oltp.publico_objetivo NOT NULL,
    filtros_json jsonb DEFAULT '{}'::jsonb
);


--
-- Name: COLUMN regla_asignacion.filtros_json; Type: COMMENT; Schema: encuestas_oltp; Owner: -
--

COMMENT ON COLUMN encuestas_oltp.regla_asignacion.filtros_json IS 'Filtros dinámicos clave-valor (ej: {"seccion": "A", "departamento": "DA"})';


--
-- Name: regla_asignacion_id_seq; Type: SEQUENCE; Schema: encuestas_oltp; Owner: -
--

CREATE SEQUENCE encuestas_oltp.regla_asignacion_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: regla_asignacion_id_seq; Type: SEQUENCE OWNED BY; Schema: encuestas_oltp; Owner: -
--

ALTER SEQUENCE encuestas_oltp.regla_asignacion_id_seq OWNED BY encuestas_oltp.regla_asignacion.id;


--
-- Name: respuesta; Type: TABLE; Schema: encuestas_oltp; Owner: -
--

CREATE TABLE encuestas_oltp.respuesta (
    id_respuesta integer NOT NULL,
    id_transaccion integer NOT NULL,
    id_pregunta integer NOT NULL,
    valor_respuesta text,
    id_opcion integer
);


--
-- Name: respuesta_borrador; Type: TABLE; Schema: encuestas_oltp; Owner: -
--

CREATE TABLE encuestas_oltp.respuesta_borrador (
    id integer NOT NULL,
    id_asignacion integer NOT NULL,
    respuestas_json jsonb NOT NULL,
    fecha_actualizacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: respuesta_borrador_id_seq; Type: SEQUENCE; Schema: encuestas_oltp; Owner: -
--

CREATE SEQUENCE encuestas_oltp.respuesta_borrador_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: respuesta_borrador_id_seq; Type: SEQUENCE OWNED BY; Schema: encuestas_oltp; Owner: -
--

ALTER SEQUENCE encuestas_oltp.respuesta_borrador_id_seq OWNED BY encuestas_oltp.respuesta_borrador.id;


--
-- Name: respuesta_id_respuesta_seq; Type: SEQUENCE; Schema: encuestas_oltp; Owner: -
--

CREATE SEQUENCE encuestas_oltp.respuesta_id_respuesta_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: respuesta_id_respuesta_seq; Type: SEQUENCE OWNED BY; Schema: encuestas_oltp; Owner: -
--

ALTER SEQUENCE encuestas_oltp.respuesta_id_respuesta_seq OWNED BY encuestas_oltp.respuesta.id_respuesta;


--
-- Name: rol_permiso; Type: TABLE; Schema: encuestas_oltp; Owner: -
--

CREATE TABLE encuestas_oltp.rol_permiso (
    id_rol encuestas_oltp.rol_admin NOT NULL,
    id_permiso integer NOT NULL
);


--
-- Name: transaccion_encuesta; Type: TABLE; Schema: encuestas_oltp; Owner: -
--

CREATE TABLE encuestas_oltp.transaccion_encuesta (
    id_transaccion integer NOT NULL,
    id_encuesta integer NOT NULL,
    fecha_finalizacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    metadatos_contexto jsonb NOT NULL,
    procesado_etl boolean DEFAULT false
);


--
-- Name: transaccion_encuesta_id_transaccion_seq; Type: SEQUENCE; Schema: encuestas_oltp; Owner: -
--

CREATE SEQUENCE encuestas_oltp.transaccion_encuesta_id_transaccion_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: transaccion_encuesta_id_transaccion_seq; Type: SEQUENCE OWNED BY; Schema: encuestas_oltp; Owner: -
--

ALTER SEQUENCE encuestas_oltp.transaccion_encuesta_id_transaccion_seq OWNED BY encuestas_oltp.transaccion_encuesta.id_transaccion;


--
-- Name: usuario_admin; Type: TABLE; Schema: encuestas_oltp; Owner: -
--

CREATE TABLE encuestas_oltp.usuario_admin (
    id_admin integer NOT NULL,
    nombre_usuario character varying(50) NOT NULL,
    clave_encriptada character varying(255) NOT NULL,
    rol encuestas_oltp.rol_admin NOT NULL,
    fecha_creacion timestamp without time zone DEFAULT now() NOT NULL,
    fecha_ultimo_login timestamp without time zone,
    activo boolean DEFAULT true NOT NULL,
    debe_cambiar_clave boolean DEFAULT false NOT NULL
);


--
-- Name: usuario_admin_id_admin_seq; Type: SEQUENCE; Schema: encuestas_oltp; Owner: -
--

CREATE SEQUENCE encuestas_oltp.usuario_admin_id_admin_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: usuario_admin_id_admin_seq; Type: SEQUENCE OWNED BY; Schema: encuestas_oltp; Owner: -
--

ALTER SEQUENCE encuestas_oltp.usuario_admin_id_admin_seq OWNED BY encuestas_oltp.usuario_admin.id_admin;


--
-- Name: usuario_permiso; Type: TABLE; Schema: encuestas_oltp; Owner: -
--

CREATE TABLE encuestas_oltp.usuario_permiso (
    id_usuario integer NOT NULL,
    id_permiso integer NOT NULL,
    tiene boolean DEFAULT true NOT NULL
);


--
-- Name: dim_contexto_academico id_dim_contexto; Type: DEFAULT; Schema: encuestas_olap; Owner: -
--

ALTER TABLE ONLY encuestas_olap.dim_contexto_academico ALTER COLUMN id_dim_contexto SET DEFAULT nextval('encuestas_olap.dim_contexto_academico_id_dim_contexto_seq'::regclass);


--
-- Name: dim_pregunta id_dim_pregunta; Type: DEFAULT; Schema: encuestas_olap; Owner: -
--

ALTER TABLE ONLY encuestas_olap.dim_pregunta ALTER COLUMN id_dim_pregunta SET DEFAULT nextval('encuestas_olap.dim_pregunta_id_dim_pregunta_seq'::regclass);


--
-- Name: dim_tiempo id_dim_tiempo; Type: DEFAULT; Schema: encuestas_olap; Owner: -
--

ALTER TABLE ONLY encuestas_olap.dim_tiempo ALTER COLUMN id_dim_tiempo SET DEFAULT nextval('encuestas_olap.dim_tiempo_id_dim_tiempo_seq'::regclass);


--
-- Name: dim_ubicacion id_dim_ubicacion; Type: DEFAULT; Schema: encuestas_olap; Owner: -
--

ALTER TABLE ONLY encuestas_olap.dim_ubicacion ALTER COLUMN id_dim_ubicacion SET DEFAULT nextval('encuestas_olap.dim_ubicacion_id_dim_ubicacion_seq'::regclass);


--
-- Name: hechos_respuestas id_hecho; Type: DEFAULT; Schema: encuestas_olap; Owner: -
--

ALTER TABLE ONLY encuestas_olap.hechos_respuestas ALTER COLUMN id_hecho SET DEFAULT nextval('encuestas_olap.hechos_respuestas_id_hecho_seq'::regclass);


--
-- Name: asignacion_usuario id; Type: DEFAULT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.asignacion_usuario ALTER COLUMN id SET DEFAULT nextval('encuestas_oltp.asignacion_usuario_id_seq'::regclass);


--
-- Name: encuesta id; Type: DEFAULT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.encuesta ALTER COLUMN id SET DEFAULT nextval('encuestas_oltp.encuesta_id_seq'::regclass);


--
-- Name: opcion_respuesta id; Type: DEFAULT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.opcion_respuesta ALTER COLUMN id SET DEFAULT nextval('encuestas_oltp.opcion_respuesta_id_seq'::regclass);


--
-- Name: permiso id_permiso; Type: DEFAULT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.permiso ALTER COLUMN id_permiso SET DEFAULT nextval('encuestas_oltp.permiso_id_permiso_seq'::regclass);


--
-- Name: plantilla_opcion_detalle id; Type: DEFAULT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.plantilla_opcion_detalle ALTER COLUMN id SET DEFAULT nextval('encuestas_oltp.plantilla_opcion_detalle_id_seq'::regclass);


--
-- Name: plantilla_opciones id; Type: DEFAULT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.plantilla_opciones ALTER COLUMN id SET DEFAULT nextval('encuestas_oltp.plantilla_opciones_id_seq'::regclass);


--
-- Name: pregunta id; Type: DEFAULT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.pregunta ALTER COLUMN id SET DEFAULT nextval('encuestas_oltp.pregunta_id_seq'::regclass);


--
-- Name: regla_asignacion id; Type: DEFAULT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.regla_asignacion ALTER COLUMN id SET DEFAULT nextval('encuestas_oltp.regla_asignacion_id_seq'::regclass);


--
-- Name: respuesta id_respuesta; Type: DEFAULT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.respuesta ALTER COLUMN id_respuesta SET DEFAULT nextval('encuestas_oltp.respuesta_id_respuesta_seq'::regclass);


--
-- Name: respuesta_borrador id; Type: DEFAULT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.respuesta_borrador ALTER COLUMN id SET DEFAULT nextval('encuestas_oltp.respuesta_borrador_id_seq'::regclass);


--
-- Name: transaccion_encuesta id_transaccion; Type: DEFAULT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.transaccion_encuesta ALTER COLUMN id_transaccion SET DEFAULT nextval('encuestas_oltp.transaccion_encuesta_id_transaccion_seq'::regclass);


--
-- Name: usuario_admin id_admin; Type: DEFAULT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.usuario_admin ALTER COLUMN id_admin SET DEFAULT nextval('encuestas_oltp.usuario_admin_id_admin_seq'::regclass);


--
-- Name: dim_contexto_academico dim_contexto_academico_pkey; Type: CONSTRAINT; Schema: encuestas_olap; Owner: -
--

ALTER TABLE ONLY encuestas_olap.dim_contexto_academico
    ADD CONSTRAINT dim_contexto_academico_pkey PRIMARY KEY (id_dim_contexto);


--
-- Name: dim_pregunta dim_pregunta_pkey; Type: CONSTRAINT; Schema: encuestas_olap; Owner: -
--

ALTER TABLE ONLY encuestas_olap.dim_pregunta
    ADD CONSTRAINT dim_pregunta_pkey PRIMARY KEY (id_dim_pregunta);


--
-- Name: dim_tiempo dim_tiempo_fecha_key; Type: CONSTRAINT; Schema: encuestas_olap; Owner: -
--

ALTER TABLE ONLY encuestas_olap.dim_tiempo
    ADD CONSTRAINT dim_tiempo_fecha_key UNIQUE (fecha);


--
-- Name: dim_tiempo dim_tiempo_pkey; Type: CONSTRAINT; Schema: encuestas_olap; Owner: -
--

ALTER TABLE ONLY encuestas_olap.dim_tiempo
    ADD CONSTRAINT dim_tiempo_pkey PRIMARY KEY (id_dim_tiempo);


--
-- Name: dim_ubicacion dim_ubicacion_pkey; Type: CONSTRAINT; Schema: encuestas_olap; Owner: -
--

ALTER TABLE ONLY encuestas_olap.dim_ubicacion
    ADD CONSTRAINT dim_ubicacion_pkey PRIMARY KEY (id_dim_ubicacion);


--
-- Name: hechos_respuestas hechos_respuestas_pkey; Type: CONSTRAINT; Schema: encuestas_olap; Owner: -
--

ALTER TABLE ONLY encuestas_olap.hechos_respuestas
    ADD CONSTRAINT hechos_respuestas_pkey PRIMARY KEY (id_hecho);


--
-- Name: dim_contexto_academico uniq_contexto; Type: CONSTRAINT; Schema: encuestas_olap; Owner: -
--

ALTER TABLE ONLY encuestas_olap.dim_contexto_academico
    ADD CONSTRAINT uniq_contexto UNIQUE (nombre_profesor, nombre_asignatura);


--
-- Name: dim_ubicacion uniq_ubicacion; Type: CONSTRAINT; Schema: encuestas_olap; Owner: -
--

ALTER TABLE ONLY encuestas_olap.dim_ubicacion
    ADD CONSTRAINT uniq_ubicacion UNIQUE (nombre_facultad, nombre_carrera, nombre_campus);


--
-- Name: asignacion_usuario asignacion_usuario_pkey; Type: CONSTRAINT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.asignacion_usuario
    ADD CONSTRAINT asignacion_usuario_pkey PRIMARY KEY (id);


--
-- Name: encuesta encuesta_pkey; Type: CONSTRAINT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.encuesta
    ADD CONSTRAINT encuesta_pkey PRIMARY KEY (id);


--
-- Name: opcion_respuesta opcion_respuesta_pkey; Type: CONSTRAINT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.opcion_respuesta
    ADD CONSTRAINT opcion_respuesta_pkey PRIMARY KEY (id);


--
-- Name: permiso permiso_codigo_key; Type: CONSTRAINT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.permiso
    ADD CONSTRAINT permiso_codigo_key UNIQUE (codigo);


--
-- Name: permiso permiso_pkey; Type: CONSTRAINT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.permiso
    ADD CONSTRAINT permiso_pkey PRIMARY KEY (id_permiso);


--
-- Name: plantilla_opcion_detalle plantilla_opcion_detalle_pkey; Type: CONSTRAINT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.plantilla_opcion_detalle
    ADD CONSTRAINT plantilla_opcion_detalle_pkey PRIMARY KEY (id);


--
-- Name: plantilla_opciones plantilla_opciones_pkey; Type: CONSTRAINT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.plantilla_opciones
    ADD CONSTRAINT plantilla_opciones_pkey PRIMARY KEY (id);


--
-- Name: pregunta pregunta_pkey; Type: CONSTRAINT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.pregunta
    ADD CONSTRAINT pregunta_pkey PRIMARY KEY (id);


--
-- Name: regla_asignacion regla_asignacion_pkey; Type: CONSTRAINT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.regla_asignacion
    ADD CONSTRAINT regla_asignacion_pkey PRIMARY KEY (id);


--
-- Name: respuesta_borrador respuesta_borrador_asignacion_id_key; Type: CONSTRAINT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.respuesta_borrador
    ADD CONSTRAINT respuesta_borrador_asignacion_id_key UNIQUE (id_asignacion);


--
-- Name: respuesta_borrador respuesta_borrador_pkey; Type: CONSTRAINT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.respuesta_borrador
    ADD CONSTRAINT respuesta_borrador_pkey PRIMARY KEY (id);


--
-- Name: respuesta respuesta_pkey; Type: CONSTRAINT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.respuesta
    ADD CONSTRAINT respuesta_pkey PRIMARY KEY (id_respuesta);


--
-- Name: rol_permiso rol_permiso_pkey; Type: CONSTRAINT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.rol_permiso
    ADD CONSTRAINT rol_permiso_pkey PRIMARY KEY (id_rol, id_permiso);


--
-- Name: transaccion_encuesta transaccion_encuesta_pkey; Type: CONSTRAINT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.transaccion_encuesta
    ADD CONSTRAINT transaccion_encuesta_pkey PRIMARY KEY (id_transaccion);


--
-- Name: asignacion_usuario uq_usuario_encuesta_contexto; Type: CONSTRAINT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.asignacion_usuario
    ADD CONSTRAINT uq_usuario_encuesta_contexto UNIQUE (id_usuario, id_encuesta, id_referencia_contexto);


--
-- Name: usuario_admin usuario_admin_pkey; Type: CONSTRAINT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.usuario_admin
    ADD CONSTRAINT usuario_admin_pkey PRIMARY KEY (id_admin);


--
-- Name: usuario_admin usuario_admin_username_key; Type: CONSTRAINT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.usuario_admin
    ADD CONSTRAINT usuario_admin_username_key UNIQUE (nombre_usuario);


--
-- Name: usuario_permiso usuario_permiso_pkey; Type: CONSTRAINT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.usuario_permiso
    ADD CONSTRAINT usuario_permiso_pkey PRIMARY KEY (id_usuario, id_permiso);


--
-- Name: idx_hechos_contexto; Type: INDEX; Schema: encuestas_olap; Owner: -
--

CREATE INDEX idx_hechos_contexto ON encuestas_olap.hechos_respuestas USING btree (id_dim_contexto);


--
-- Name: idx_hechos_tiempo; Type: INDEX; Schema: encuestas_olap; Owner: -
--

CREATE INDEX idx_hechos_tiempo ON encuestas_olap.hechos_respuestas USING btree (id_dim_tiempo);


--
-- Name: idx_asignacion_usuario_estado; Type: INDEX; Schema: encuestas_oltp; Owner: -
--

CREATE INDEX idx_asignacion_usuario_estado ON encuestas_oltp.asignacion_usuario USING btree (id_usuario, estado);


--
-- Name: idx_encuesta_id_admin_creacion; Type: INDEX; Schema: encuestas_oltp; Owner: -
--

CREATE INDEX idx_encuesta_id_admin_creacion ON encuestas_oltp.encuesta USING btree (usuario_creacion);


--
-- Name: idx_encuesta_id_admin_modificacion; Type: INDEX; Schema: encuestas_oltp; Owner: -
--

CREATE INDEX idx_encuesta_id_admin_modificacion ON encuestas_oltp.encuesta USING btree (usuario_modificacion);


--
-- Name: idx_permiso_codigo; Type: INDEX; Schema: encuestas_oltp; Owner: -
--

CREATE INDEX idx_permiso_codigo ON encuestas_oltp.permiso USING btree (codigo);


--
-- Name: idx_rol_permiso_rol; Type: INDEX; Schema: encuestas_oltp; Owner: -
--

CREATE INDEX idx_rol_permiso_rol ON encuestas_oltp.rol_permiso USING btree (id_rol);


--
-- Name: idx_usuario_permiso_usuario; Type: INDEX; Schema: encuestas_oltp; Owner: -
--

CREATE INDEX idx_usuario_permiso_usuario ON encuestas_oltp.usuario_permiso USING btree (id_usuario);


--
-- Name: hechos_respuestas hechos_respuestas_id_dim_contexto_fkey; Type: FK CONSTRAINT; Schema: encuestas_olap; Owner: -
--

ALTER TABLE ONLY encuestas_olap.hechos_respuestas
    ADD CONSTRAINT hechos_respuestas_id_dim_contexto_fkey FOREIGN KEY (id_dim_contexto) REFERENCES encuestas_olap.dim_contexto_academico(id_dim_contexto);


--
-- Name: hechos_respuestas hechos_respuestas_id_dim_pregunta_fkey; Type: FK CONSTRAINT; Schema: encuestas_olap; Owner: -
--

ALTER TABLE ONLY encuestas_olap.hechos_respuestas
    ADD CONSTRAINT hechos_respuestas_id_dim_pregunta_fkey FOREIGN KEY (id_dim_pregunta) REFERENCES encuestas_olap.dim_pregunta(id_dim_pregunta);


--
-- Name: hechos_respuestas hechos_respuestas_id_dim_tiempo_fkey; Type: FK CONSTRAINT; Schema: encuestas_olap; Owner: -
--

ALTER TABLE ONLY encuestas_olap.hechos_respuestas
    ADD CONSTRAINT hechos_respuestas_id_dim_tiempo_fkey FOREIGN KEY (id_dim_tiempo) REFERENCES encuestas_olap.dim_tiempo(id_dim_tiempo);


--
-- Name: hechos_respuestas hechos_respuestas_id_dim_ubicacion_fkey; Type: FK CONSTRAINT; Schema: encuestas_olap; Owner: -
--

ALTER TABLE ONLY encuestas_olap.hechos_respuestas
    ADD CONSTRAINT hechos_respuestas_id_dim_ubicacion_fkey FOREIGN KEY (id_dim_ubicacion) REFERENCES encuestas_olap.dim_ubicacion(id_dim_ubicacion);


--
-- Name: asignacion_usuario asignacion_usuario_encuesta_id_fkey; Type: FK CONSTRAINT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.asignacion_usuario
    ADD CONSTRAINT asignacion_usuario_encuesta_id_fkey FOREIGN KEY (id_encuesta) REFERENCES encuestas_oltp.encuesta(id);


--
-- Name: encuesta fk_encuesta_admin_creacion; Type: FK CONSTRAINT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.encuesta
    ADD CONSTRAINT fk_encuesta_admin_creacion FOREIGN KEY (usuario_creacion) REFERENCES encuestas_oltp.usuario_admin(id_admin) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: encuesta fk_encuesta_admin_modificacion; Type: FK CONSTRAINT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.encuesta
    ADD CONSTRAINT fk_encuesta_admin_modificacion FOREIGN KEY (usuario_modificacion) REFERENCES encuestas_oltp.usuario_admin(id_admin) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: opcion_respuesta opcion_respuesta_pregunta_id_fkey; Type: FK CONSTRAINT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.opcion_respuesta
    ADD CONSTRAINT opcion_respuesta_pregunta_id_fkey FOREIGN KEY (id_pregunta) REFERENCES encuestas_oltp.pregunta(id) ON DELETE CASCADE;


--
-- Name: plantilla_opcion_detalle plantilla_opcion_detalle_id_plantilla_fkey; Type: FK CONSTRAINT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.plantilla_opcion_detalle
    ADD CONSTRAINT plantilla_opcion_detalle_id_plantilla_fkey FOREIGN KEY (id_plantilla) REFERENCES encuestas_oltp.plantilla_opciones(id) ON DELETE CASCADE;


--
-- Name: pregunta pregunta_encuesta_id_fkey; Type: FK CONSTRAINT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.pregunta
    ADD CONSTRAINT pregunta_encuesta_id_fkey FOREIGN KEY (id_encuesta) REFERENCES encuestas_oltp.encuesta(id) ON DELETE CASCADE;


--
-- Name: regla_asignacion regla_asignacion_encuesta_id_fkey; Type: FK CONSTRAINT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.regla_asignacion
    ADD CONSTRAINT regla_asignacion_encuesta_id_fkey FOREIGN KEY (id_encuesta) REFERENCES encuestas_oltp.encuesta(id) ON DELETE CASCADE;


--
-- Name: respuesta_borrador respuesta_borrador_asignacion_id_fkey; Type: FK CONSTRAINT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.respuesta_borrador
    ADD CONSTRAINT respuesta_borrador_asignacion_id_fkey FOREIGN KEY (id_asignacion) REFERENCES encuestas_oltp.asignacion_usuario(id) ON DELETE CASCADE;


--
-- Name: respuesta respuesta_id_transaccion_fkey; Type: FK CONSTRAINT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.respuesta
    ADD CONSTRAINT respuesta_id_transaccion_fkey FOREIGN KEY (id_transaccion) REFERENCES encuestas_oltp.transaccion_encuesta(id_transaccion) ON DELETE CASCADE;


--
-- Name: respuesta respuesta_opcion_id_fkey; Type: FK CONSTRAINT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.respuesta
    ADD CONSTRAINT respuesta_opcion_id_fkey FOREIGN KEY (id_opcion) REFERENCES encuestas_oltp.opcion_respuesta(id);


--
-- Name: respuesta respuesta_pregunta_id_fkey; Type: FK CONSTRAINT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.respuesta
    ADD CONSTRAINT respuesta_pregunta_id_fkey FOREIGN KEY (id_pregunta) REFERENCES encuestas_oltp.pregunta(id);


--
-- Name: rol_permiso rol_permiso_id_permiso_fkey; Type: FK CONSTRAINT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.rol_permiso
    ADD CONSTRAINT rol_permiso_id_permiso_fkey FOREIGN KEY (id_permiso) REFERENCES encuestas_oltp.permiso(id_permiso) ON DELETE CASCADE;


--
-- Name: transaccion_encuesta transaccion_encuesta_encuesta_id_fkey; Type: FK CONSTRAINT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.transaccion_encuesta
    ADD CONSTRAINT transaccion_encuesta_encuesta_id_fkey FOREIGN KEY (id_encuesta) REFERENCES encuestas_oltp.encuesta(id);


--
-- Name: usuario_permiso usuario_permiso_id_permiso_fkey; Type: FK CONSTRAINT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.usuario_permiso
    ADD CONSTRAINT usuario_permiso_id_permiso_fkey FOREIGN KEY (id_permiso) REFERENCES encuestas_oltp.permiso(id_permiso) ON DELETE CASCADE;


--
-- Name: usuario_permiso usuario_permiso_id_usuario_fkey; Type: FK CONSTRAINT; Schema: encuestas_oltp; Owner: -
--

ALTER TABLE ONLY encuestas_oltp.usuario_permiso
    ADD CONSTRAINT usuario_permiso_id_usuario_fkey FOREIGN KEY (id_usuario) REFERENCES encuestas_oltp.usuario_admin(id_admin) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict hSQaGl8JxKMbjNdxIRrCT3StUBNKlsHhU7p1hLK4c00Te9PBYISDmoHbuCoL7J6

