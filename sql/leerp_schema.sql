-- ============================================================
-- LEERP — Esquema base v1.0 (PostgreSQL / Neon Cloud)
-- Generalizado a partir del modelo de GuateCompost ERP
-- ============================================================
-- CAMBIOS PRINCIPALES vs. GuateCompost (decisiones del equipo):
--   1. Tabla "usuarios" — login con password hasheado (bcrypt)
--   2. Tabla "config_empresa" — datos superficiales por cliente
--      (nombre, moneda, logo) — un proyecto Neon aislado por cliente
--   3. "activo" + auditoría como ESTÁNDAR de plantilla en todo
--      maestro, no como parche posterior (Sesión 7 de Guatecompost)
--   4. Catálogos controlados unidad_medida / categoria en vez de
--      texto libre — consistencia para BI multi-cliente
--   5. producto.tipo distingue 'producto' vs 'servicio'
--   6. Fechas como tipo DATE/TIMESTAMP nativo (Guatecompost las
--      guardaba como TEXT en SQLite — ya no aplica en Postgres)
--   7. Toda transacción referencia id_usuario — trazabilidad de
--      quién registró cada venta/compra/gasto
--   8. Montos en NUMERIC(15,2) — nunca float para dinero
-- ============================================================

-- ------------------------------------------------------------
-- CONFIGURACIÓN DEL CLIENTE (1 sola fila por instancia)
-- ------------------------------------------------------------
CREATE TABLE config_empresa (
    id_config       SERIAL PRIMARY KEY,
    nombre_empresa  VARCHAR(150) NOT NULL,
    pais            VARCHAR(60),
    moneda_codigo   CHAR(3) NOT NULL DEFAULT 'GTQ',   -- ISO 4217
    moneda_simbolo  VARCHAR(5) NOT NULL DEFAULT 'Q',
    timezone        VARCHAR(50) DEFAULT 'America/Guatemala',
    logo_url        VARCHAR(255),
    fecha_creacion  TIMESTAMP NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------
-- USUARIOS (login al ERP — creados solo por el administrador)
-- ------------------------------------------------------------
CREATE TABLE usuarios (
    id_usuario      SERIAL PRIMARY KEY,
    nombre_completo VARCHAR(150) NOT NULL,
    usuario         VARCHAR(50) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,            -- bcrypt, nunca texto plano
    rol             VARCHAR(20) NOT NULL DEFAULT 'captura'
                        CHECK (rol IN ('admin','captura','analista','visor')),
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion  TIMESTAMP NOT NULL DEFAULT now(),
    ultimo_acceso   TIMESTAMP
);

-- ------------------------------------------------------------
-- CATÁLOGOS CONTROLADOS
-- ------------------------------------------------------------
CREATE TABLE unidad_medida (
    id_unidad    SERIAL PRIMARY KEY,
    nombre       VARCHAR(30) UNIQUE NOT NULL,         -- Kilogramo, Unidad, Hora
    abreviatura  VARCHAR(10)                          -- kg, u, hr
);

CREATE TABLE categoria (
    id_categoria SERIAL PRIMARY KEY,
    nombre       VARCHAR(60) UNIQUE NOT NULL,
    activo       BOOLEAN NOT NULL DEFAULT TRUE
);

-- ------------------------------------------------------------
-- MAESTROS
-- ------------------------------------------------------------
CREATE TABLE producto (
    id_producto      SERIAL PRIMARY KEY,
    nombre           VARCHAR(150) NOT NULL,
    descripcion      TEXT,
    tipo             VARCHAR(20) NOT NULL DEFAULT 'producto'
                         CHECK (tipo IN ('producto','servicio')),
    id_categoria     INT REFERENCES categoria(id_categoria),
    id_unidad_medida INT REFERENCES unidad_medida(id_unidad),
    costo            NUMERIC(15,2) DEFAULT 0,
    precio           NUMERIC(15,2) DEFAULT 0,
    activo           BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion   TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE cliente (
    id_cliente      SERIAL PRIMARY KEY,
    nombre          VARCHAR(150) NOT NULL,
    nit             VARCHAR(20),
    telefono        VARCHAR(20),
    correo          VARCHAR(100),
    direccion       VARCHAR(200),
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion  TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE proveedor (
    id_proveedor    SERIAL PRIMARY KEY,
    nombre          VARCHAR(150) NOT NULL,
    contacto        VARCHAR(100),
    nit             VARCHAR(20),
    telefono        VARCHAR(20),
    correo          VARCHAR(100),
    direccion       VARCHAR(200),
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion  TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE insumo (
    id_insumo        SERIAL PRIMARY KEY,
    nombre           VARCHAR(150) NOT NULL,
    descripcion      TEXT,
    id_unidad_medida INT REFERENCES unidad_medida(id_unidad),
    costo            NUMERIC(15,2) DEFAULT 0,
    activo           BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion   TIMESTAMP NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------
-- INVENTARIO (stock calculado — misma lógica de Guatecompost)
-- ------------------------------------------------------------
CREATE TABLE inventario_inicial (
    id_producto  INT REFERENCES producto(id_producto),
    cantidad     NUMERIC(15,2) NOT NULL,
    fecha_corte  DATE NOT NULL,
    PRIMARY KEY (id_producto, fecha_corte)
);

-- ------------------------------------------------------------
-- VENTAS (cabecera / detalle)
-- ------------------------------------------------------------
CREATE TABLE venta_cabecera (
    id_venta     SERIAL PRIMARY KEY,
    fecha_venta  DATE NOT NULL DEFAULT CURRENT_DATE,
    id_cliente   INT REFERENCES cliente(id_cliente),
    id_usuario   INT REFERENCES usuarios(id_usuario)
);

CREATE TABLE venta_detalle (
    id_detalle       SERIAL PRIMARY KEY,
    id_venta         INT REFERENCES venta_cabecera(id_venta) ON DELETE CASCADE,
    id_producto      INT REFERENCES producto(id_producto),
    cantidad         NUMERIC(15,2) NOT NULL,
    precio_unitario  NUMERIC(15,2) NOT NULL,
    UNIQUE (id_venta, id_producto)
);

-- ------------------------------------------------------------
-- COMPRAS (cabecera / detalle)
-- ------------------------------------------------------------
CREATE TABLE compra_cabecera (
    id_compra     SERIAL PRIMARY KEY,
    fecha_compra  DATE NOT NULL DEFAULT CURRENT_DATE,
    id_proveedor  INT REFERENCES proveedor(id_proveedor),
    id_usuario    INT REFERENCES usuarios(id_usuario)
);

CREATE TABLE compra_detalle (
    id_detalle       SERIAL PRIMARY KEY,
    id_compra        INT REFERENCES compra_cabecera(id_compra) ON DELETE CASCADE,
    id_producto      INT REFERENCES producto(id_producto),
    cantidad         NUMERIC(15,2) NOT NULL,
    costo_unitario   NUMERIC(15,2) NOT NULL,
    UNIQUE (id_compra, id_producto)
);

-- ------------------------------------------------------------
-- GASTOS OPERATIVOS (cabecera / detalle)
-- ------------------------------------------------------------
CREATE TABLE gasto_cabecera (
    id_gasto      SERIAL PRIMARY KEY,
    fecha_gasto   DATE NOT NULL DEFAULT CURRENT_DATE,
    id_proveedor  INT REFERENCES proveedor(id_proveedor),
    descripcion   TEXT,
    id_usuario    INT REFERENCES usuarios(id_usuario)
);

CREATE TABLE gasto_detalle (
    id_detalle      SERIAL PRIMARY KEY,
    id_gasto        INT REFERENCES gasto_cabecera(id_gasto) ON DELETE CASCADE,
    id_insumo       INT REFERENCES insumo(id_insumo),
    cantidad        NUMERIC(15,2) NOT NULL,
    costo_unitario  NUMERIC(15,2) NOT NULL
);

-- ------------------------------------------------------------
-- Semilla mínima: catálogos base + usuario admin inicial
-- (el password_hash de ejemplo debe regenerarse con bcrypt real
--  antes de usarse — esto es solo un placeholder de estructura)
-- ------------------------------------------------------------
INSERT INTO unidad_medida (nombre, abreviatura) VALUES
    ('Unidad', 'u'), ('Kilogramo', 'kg'), ('Libra', 'lb'), ('Hora', 'hr');

INSERT INTO config_empresa (nombre_empresa, pais, moneda_codigo, moneda_simbolo) VALUES
    ('Nombre del Cliente', 'Guatemala', 'GTQ', 'Q');