-- ============================================================
-- LEERP — Esquema base v1.1 (PostgreSQL / Neon Cloud)
-- Generalizado a partir del modelo de GuateCompost ERP
-- ============================================================
-- CAMBIOS PRINCIPALES vs. v1.0 (sesión de actualización):
--   1. codigo_* en maestros y transaccionales (cabecera) — columna
--      GENERATED ALWAYS AS, nunca se inserta manualmente, nunca se
--      usa como foreign key (eso lo sigue siendo el id_ numérico).
--      Los *_detalle NO llevan codigo_ propio — no tienen identidad
--      para el usuario fuera de su cabecera.
--   2. id_usuario_creacion agregado a los 4 maestros (Producto,
--      Cliente, Proveedor, Insumo) — antes solo existía en las
--      transaccionales como id_usuario. Mismo propósito: trazabilidad
--      de quién creó el registro.
--   3. inventario_inicial → reemplazada por movimiento_inventario
--      (Kardex). El stock ya no se calcula con una fórmula
--      (inicial + compras - ventas, heredado de Guatecompost) sino
--      que se registra como historial de movimientos individuales.
--      Permite ajustes manuales auditables (mermas, conteos físicos)
--      sin editar la base de datos a mano.
-- ============================================================
-- CAMBIOS HEREDADOS DE v1.0 (ver Guatecompost para contexto):
--   - usuarios con password hasheado (bcrypt)
--   - config_empresa por cliente (1 fila, proyecto Neon aislado)
--   - activo + auditoría como estándar en todo maestro
--   - catálogos controlados unidad_medida / categoria
--   - producto.tipo distingue 'producto' vs 'servicio'
--   - fechas como DATE/TIMESTAMP nativo de Postgres
--   - montos en NUMERIC(15,2), nunca float
-- ============================================================

-- ------------------------------------------------------------
-- CONFIGURACIÓN DEL CLIENTE (1 sola fila por instancia)
-- Sin codigo_ ni id_usuario_creacion — no aplica, fila única de sistema.
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
-- Sin codigo_ — el usuario se identifica por su campo "usuario" (login),
-- no necesita un código adicional tipo USR-0001.
-- ------------------------------------------------------------
CREATE TABLE usuarios (
    id_usuario      SERIAL PRIMARY KEY,
    nombre_completo VARCHAR(150) NOT NULL,
    usuario         VARCHAR(50) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,            -- bcrypt, nunca texto plano
    rol             VARCHAR(20) NOT NULL DEFAULT 'captura' CHECK (rol IN ('admin','captura','analista','visor')),
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion  TIMESTAMP NOT NULL DEFAULT now(),
    ultimo_acceso   TIMESTAMP
);

-- ------------------------------------------------------------
-- CATÁLOGOS CONTROLADOS
-- Sin codigo_ ni id_usuario_creacion — catálogos de sistema, no
-- registros operativos que un usuario "crea" en el día a día.
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
-- Todos llevan: codigo_* (generado, solo lectura) + id_usuario_creacion
-- ------------------------------------------------------------
CREATE TABLE producto (
    id_producto          SERIAL PRIMARY KEY,
    codigo_producto      VARCHAR(20) GENERATED ALWAYS AS('PRD-' || LPAD(id_producto::text, 4, '0')) STORED,
    nombre               VARCHAR(150) NOT NULL,
    descripcion          TEXT,
    tipo                 VARCHAR(20) NOT NULL DEFAULT 'producto' CHECK (tipo IN ('producto','servicio')),
    id_categoria         INT REFERENCES categoria(id_categoria),
    id_unidad_medida     INT REFERENCES unidad_medida(id_unidad),
    costo                NUMERIC(15,2) DEFAULT 0,
    precio               NUMERIC(15,2) DEFAULT 0,
    activo               BOOLEAN NOT NULL DEFAULT TRUE,
    id_usuario_creacion  INT REFERENCES usuarios(id_usuario),
    fecha_creacion       TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE cliente (
    id_cliente            SERIAL PRIMARY KEY,
    codigo_cliente        VARCHAR(20) GENERATED ALWAYS AS('CLI-' || LPAD(id_cliente::text, 4, '0')) STORED,
    nombre                VARCHAR(150) NOT NULL,
    nit                   VARCHAR(20),
    telefono              VARCHAR(20),
    correo                VARCHAR(100),
    direccion             VARCHAR(200),
    activo                BOOLEAN NOT NULL DEFAULT TRUE,
    id_usuario_creacion   INT REFERENCES usuarios(id_usuario),
    fecha_creacion        TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE proveedor (
    id_proveedor           SERIAL PRIMARY KEY,
    codigo_proveedor       VARCHAR(20) GENERATED ALWAYS AS('PRV-' || LPAD(id_proveedor::text, 4, '0')) STORED,
    nombre                 VARCHAR(150) NOT NULL,
    contacto               VARCHAR(100),
    nit                    VARCHAR(20),
    telefono               VARCHAR(20),
    correo                 VARCHAR(100),
    direccion              VARCHAR(200),
    activo                 BOOLEAN NOT NULL DEFAULT TRUE,
    id_usuario_creacion    INT REFERENCES usuarios(id_usuario),
    fecha_creacion         TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE insumo (
    id_insumo              SERIAL PRIMARY KEY,
    codigo_insumo          VARCHAR(20) GENERATED ALWAYS AS('INS-' || LPAD(id_insumo::text, 4, '0')) STORED,
    nombre                 VARCHAR(150) NOT NULL,
    descripcion            TEXT,
    id_unidad_medida       INT REFERENCES unidad_medida(id_unidad),
    costo                  NUMERIC(15,2) DEFAULT 0,
    activo                 BOOLEAN NOT NULL DEFAULT TRUE,
    id_usuario_creacion    INT REFERENCES usuarios(id_usuario),
    fecha_creacion         TIMESTAMP NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------
-- INVENTARIO (Kardex — registro de movimientos, NO fórmula calculada)
-- ------------------------------------------------------------
-- Reemplaza a "inventario_inicial" de v1.0. El stock actual de un
-- producto = SUM(cantidad) de sus movimientos, aplicando el signo
-- según tipo_movimiento (ver función helper más abajo).
--
-- tipo_movimiento:
--   'inventario_inicial'  -> entrada (carga inicial al arrancar el cliente)
--   'entrada_compra'      -> entrada (generada automáticamente desde Compras)
--   'salida_venta'        -> salida  (generada automáticamente desde Ventas)
--   'ajuste_positivo'     -> entrada (conteo físico encontró más stock)
--   'ajuste_negativo'     -> salida  (merma, daño, robo, conteo físico con faltante)
--
-- referencia_tipo / referencia_id apuntan opcionalmente a la transacción
-- de origen (ej. 'venta' / id_venta) — permite trazar "este movimiento
-- vino de la venta VTA-0047" sin duplicar lógica de relación por tipo.
-- ------------------------------------------------------------
CREATE TABLE movimiento_inventario (
    id_movimiento          SERIAL PRIMARY KEY,
    codigo_movimiento      VARCHAR(20) GENERATED ALWAYS AS('MOV-' || LPAD(id_movimiento::text, 5, '0')) STORED,
    id_producto            INT NOT NULL REFERENCES producto(id_producto),
    tipo_movimiento        VARCHAR(20) NOT NULL CHECK (tipo_movimiento IN ('inventario_inicial', 'entrada_compra', 'salida_venta','ajuste_positivo', 'ajuste_negativo')),
    cantidad               NUMERIC(15,2) NOT NULL CHECK (cantidad > 0),
    fecha_movimiento       TIMESTAMP NOT NULL DEFAULT now(),
    referencia_tipo        VARCHAR(20),
    referencia_id          INT,
    nota                   TEXT,
    id_usuario_creacion    INT NOT NULL REFERENCES usuarios(id_usuario)
);

CREATE INDEX idx_movimiento_producto ON movimiento_inventario(id_producto);

-- ------------------------------------------------------------
-- VENTAS (cabecera / detalle)
-- Cabecera: codigo_ + id_usuario (ya existía, se mantiene su nombre
-- original para no romper lo ya construido). Detalle: sin codigo_,
-- sin id_usuario_creacion propio (hereda la autoría de su cabecera).
-- ------------------------------------------------------------
CREATE TABLE venta_cabecera (
    id_venta       SERIAL PRIMARY KEY,
    codigo_venta   VARCHAR(20) GENERATED ALWAYS AS('VTA-' || LPAD(id_venta::text, 4, '0')) STORED,
    fecha_venta    DATE NOT NULL DEFAULT CURRENT_DATE,
    id_cliente     INT REFERENCES cliente(id_cliente),
    id_usuario     INT REFERENCES usuarios(id_usuario)
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
    id_compra      SERIAL PRIMARY KEY,
    codigo_compra  VARCHAR(20) GENERATED ALWAYS AS('CMP-' || LPAD(id_compra::text, 4, '0')) STORED,
    fecha_compra   DATE NOT NULL DEFAULT CURRENT_DATE,
    id_proveedor   INT REFERENCES proveedor(id_proveedor),
    id_usuario     INT REFERENCES usuarios(id_usuario)
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
    id_gasto       SERIAL PRIMARY KEY,
    codigo_gasto   VARCHAR(20) GENERATED ALWAYS AS('GAS-' || LPAD(id_gasto::text, 4, '0')) STORED,
    fecha_gasto    DATE NOT NULL DEFAULT CURRENT_DATE,
    id_proveedor   INT REFERENCES proveedor(id_proveedor),
    descripcion    TEXT,
    id_usuario     INT REFERENCES usuarios(id_usuario)
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