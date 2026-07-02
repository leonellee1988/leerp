# db.py
# Capa de datos — conexión a PostgreSQL (Neon) y queries.
#
# Cada módulo (productos.py, clientes.py, ventas.py, etc.) llama a
# estas funciones, nunca abre su propia conexión directamente — así,
# si algo de la conexión cambia, solo se toca este archivo.
#
# DECISIÓN ESTRUCTURAL: todas las funciones usan RealDictCursor.
# Esto hace que cada fila devuelta sea un dict con nombres de columna
# como llaves (r["nombre"] en vez de r[3]), eliminando permanentemente
# el riesgo de KeyError por índices desincronizados al agregar columnas
# al SELECT. Aplica a todas las funciones actuales y futuras.

import os

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

from utils.auth_utils import verificar_password

load_dotenv()


def get_connection():
    """Abre una conexión nueva a la base de datos Neon."""
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.environ.get("DB_PORT", 5432),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        sslmode=os.environ.get("DB_SSLMODE", "require"),
    )


# ------------------------------------------------------------
# Autenticación
# Excepción: verificar_login usa cursor estándar porque necesita
# acceder a password_hash por índice para verificarlo con bcrypt
# antes de construir el dict de retorno. El resto usa RealDictCursor.
# ------------------------------------------------------------

def verificar_login(usuario, password):
    """Valida usuario/contraseña contra la tabla usuarios.
    Devuelve un dict con los datos del usuario si es válido, o None
    si el usuario no existe, está inactivo, o la contraseña no coincide."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id_usuario, nombre_completo, password_hash, rol "
                "FROM usuarios WHERE usuario = %s AND activo = TRUE",
                (usuario,)
            )
            row = cur.fetchone()

    if row and verificar_password(password, row[2]):
        return {"id_usuario": row[0], "nombre": row[1], "rol": row[3]}
    return None


def get_config_empresa():
    """Devuelve los datos de configuración del cliente (1 sola fila)."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT nombre_empresa, pais, moneda_codigo, moneda_simbolo, logo_url "
                "FROM config_empresa LIMIT 1"
            )
            row = cur.fetchone()

    if not row:
        return None
    return {
        "nombre_empresa": row["nombre_empresa"],
        "pais": row["pais"],
        "moneda_codigo": row["moneda_codigo"],
        "moneda_simbolo": row["moneda_simbolo"],
        "logo_url": row["logo_url"],
    }


# ------------------------------------------------------------
# Catálogos (usados por varios módulos, no solo Productos)
# ------------------------------------------------------------

def get_categorias():
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id_categoria, nombre FROM categoria WHERE activo = TRUE ORDER BY nombre")
            rows = cur.fetchall()
    return [{"id_categoria": r["id_categoria"], "nombre": r["nombre"]} for r in rows]


def get_unidades_medida():
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id_unidad, nombre FROM unidad_medida ORDER BY nombre")
            rows = cur.fetchall()
    return [{"id_unidad": r["id_unidad"], "nombre": r["nombre"]} for r in rows]


# ------------------------------------------------------------
# Productos
# ------------------------------------------------------------

def get_productos(busqueda="", id_categoria=None, estado="todos"):
    """Lista de productos para la pantalla Consultar, con filtros opcionales.
    'busqueda' acepta nombre parcial o código exacto/parcial (ej. 'PRD-0042').
    Devuelve todos los campos operativos + auditoría (fecha_creacion, creado_por)
    para que el CSV de descarga siempre incluya trazabilidad completa."""
    condiciones = []
    parametros = []

    busqueda = busqueda.strip()
    if busqueda:
        condiciones.append("(p.nombre ILIKE %s OR p.codigo_producto ILIKE %s)")
        parametros.append(f"%{busqueda}%")
        parametros.append(f"%{busqueda}%")

    if id_categoria:
        condiciones.append("p.id_categoria = %s")
        parametros.append(id_categoria)

    if estado == "activos":
        condiciones.append("p.activo = TRUE")
    elif estado == "inactivos":
        condiciones.append("p.activo = FALSE")

    where_sql = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""

    query = f"""
        SELECT
            p.id_producto,
            p.codigo_producto,
            p.nombre,
            p.descripcion,
            c.nombre        AS categoria,
            u.nombre        AS unidad,
            p.costo,
            p.precio,
            p.activo,
            p.fecha_creacion,
            us.nombre_completo AS creado_por
        FROM producto p
        LEFT JOIN categoria     c  ON p.id_categoria        = c.id_categoria
        LEFT JOIN unidad_medida u  ON p.id_unidad_medida    = u.id_unidad
        LEFT JOIN usuarios      us ON p.id_usuario_creacion = us.id_usuario
        {where_sql}
        ORDER BY p.id_producto DESC
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, parametros)
            rows = cur.fetchall()

    return [
        {
            "id_producto":      r["id_producto"],
            "codigo_producto":  r["codigo_producto"],
            "nombre":           r["nombre"],
            "descripcion":      r["descripcion"] or "—",
            "categoria":        r["categoria"]   or "—",
            "unidad":           r["unidad"]       or "—",
            "costo":            r["costo"],
            "precio":           r["precio"],
            "activo":           r["activo"],
            "fecha_creacion":   r["fecha_creacion"].strftime("%Y-%m-%d %H:%M") if r["fecha_creacion"] else "—",
            "creado_por":       r["creado_por"] or "—",
        }
        for r in rows
    ]


def get_producto_by_id(id_producto):
    """Devuelve todos los campos editables de un producto por su ID.
    Usado por el formulario de edición para precargar los valores actuales."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """SELECT id_producto, codigo_producto, nombre, descripcion,
                          tipo, id_categoria, id_unidad_medida, costo, precio, activo
                   FROM producto
                   WHERE id_producto = %s""",
                (id_producto,)
            )
            row = cur.fetchone()
    if not row:
        return None
    return {
        "id_producto":      row["id_producto"],
        "codigo_producto":  row["codigo_producto"],
        "nombre":           row["nombre"],
        "descripcion":      row["descripcion"],
        "tipo":             row["tipo"],
        "id_categoria":     row["id_categoria"],
        "id_unidad_medida": row["id_unidad_medida"],
        "costo":            row["costo"],
        "precio":           row["precio"],
        "activo":           row["activo"],
    }


def insert_producto(nombre, descripcion, tipo, id_categoria, id_unidad_medida,
                    costo, precio, activo, id_usuario_creacion):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO producto
                   (nombre, descripcion, tipo, id_categoria, id_unidad_medida,
                    costo, precio, activo, id_usuario_creacion)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (nombre, descripcion, tipo, id_categoria, id_unidad_medida,
                 costo, precio, activo, id_usuario_creacion)
            )
        conn.commit()


def update_producto(id_producto, nombre, descripcion, tipo, id_categoria,
                    id_unidad_medida, costo, precio, activo):
    """Actualiza un producto existente.
    costo = costo de adquisición, precio = precio de venta. No mezclarlos."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE producto
                   SET nombre=%s, descripcion=%s, tipo=%s,
                       id_categoria=%s, id_unidad_medida=%s,
                       costo=%s, precio=%s, activo=%s
                   WHERE id_producto=%s""",
                (nombre, descripcion, tipo, id_categoria, id_unidad_medida,
                 costo, precio, activo, id_producto)
            )
        conn.commit()


# ------------------------------------------------------------
# Clientes
# ------------------------------------------------------------

def get_clientes(busqueda="", estado="todos"):
    condiciones = []
    parametros = []

    busqueda = busqueda.strip()
    if busqueda:
        condiciones.append("(c.nombre ILIKE %s OR c.codigo_cliente ILIKE %s OR c.nit ILIKE %s)")
        parametros.extend([f"%{busqueda}%", f"%{busqueda}%", f"%{busqueda}%"])

    if estado == "activos":
        condiciones.append("c.activo = TRUE")
    elif estado == "inactivos":
        condiciones.append("c.activo = FALSE")

    where_sql = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""

    query = f"""
        SELECT
            c.id_cliente,
            c.codigo_cliente,
            c.nombre,
            c.nit,
            c.telefono,
            c.correo,
            c.direccion,
            c.activo,
            c.fecha_creacion,
            us.nombre_completo AS creado_por
        FROM cliente c
        LEFT JOIN usuarios us ON c.id_usuario_creacion = us.id_usuario
        {where_sql}
        ORDER BY c.id_cliente DESC
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, parametros)
            rows = cur.fetchall()

    return [
        {
            "id_cliente":     r["id_cliente"],
            "codigo_cliente": r["codigo_cliente"],
            "nombre":         r["nombre"],
            "nit":            r["nit"]       or "—",
            "telefono":       r["telefono"]  or "—",
            "correo":         r["correo"]    or "—",
            "direccion":      r["direccion"] or "—",
            "activo":         r["activo"],
            "fecha_creacion": r["fecha_creacion"].strftime("%Y-%m-%d %H:%M") if r["fecha_creacion"] else "—",
            "creado_por":     r["creado_por"] or "—",
        }
        for r in rows
    ]


def get_cliente_by_id(id_cliente):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """SELECT id_cliente, codigo_cliente, nombre, nit,
                          telefono, correo, direccion, activo
                   FROM cliente WHERE id_cliente = %s""",
                (id_cliente,)
            )
            row = cur.fetchone()
    if not row:
        return None
    return dict(row)


def get_cliente_by_codigo(codigo_cliente):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """SELECT id_cliente, codigo_cliente, nombre, nit,
                          telefono, correo, direccion, activo
                   FROM cliente WHERE codigo_cliente ILIKE %s""",
                (f"%{codigo_cliente.strip()}%",)
            )
            row = cur.fetchone()
    if not row:
        return None
    return dict(row)


def insert_cliente(nombre, nit, telefono, correo, direccion, activo, id_usuario_creacion):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO cliente
                   (nombre, nit, telefono, correo, direccion, activo, id_usuario_creacion)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (nombre, nit, telefono, correo, direccion, activo, id_usuario_creacion)
            )
        conn.commit()


def update_cliente(id_cliente, nombre, nit, telefono, correo, direccion, activo):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE cliente
                   SET nombre=%s, nit=%s, telefono=%s,
                       correo=%s, direccion=%s, activo=%s
                   WHERE id_cliente=%s""",
                (nombre, nit, telefono, correo, direccion, activo, id_cliente)
            )
        conn.commit()

# ------------------------------------------------------------
# Proveedores
# ------------------------------------------------------------

def get_proveedores(busqueda="", estado="todos"):
    condiciones = []
    parametros = []
    busqueda = busqueda.strip()
    if busqueda:
        condiciones.append("(p.nombre ILIKE %s OR p.codigo_proveedor ILIKE %s OR p.nit ILIKE %s)")
        parametros.extend([f"%{busqueda}%", f"%{busqueda}%", f"%{busqueda}%"])
    if estado == "activos":
        condiciones.append("p.activo = TRUE")
    elif estado == "inactivos":
        condiciones.append("p.activo = FALSE")
    where_sql = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""
    query = f"""
        SELECT p.id_proveedor, p.codigo_proveedor, p.nombre, p.contacto,
               p.nit, p.telefono, p.correo, p.direccion, p.activo,
               p.fecha_creacion, us.nombre_completo AS creado_por
        FROM proveedor p
        LEFT JOIN usuarios us ON p.id_usuario_creacion = us.id_usuario
        {where_sql}
        ORDER BY p.id_proveedor DESC
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, parametros)
            rows = cur.fetchall()
    return [
        {
            "id_proveedor":     r["id_proveedor"],
            "codigo_proveedor": r["codigo_proveedor"],
            "nombre":           r["nombre"],
            "contacto":         r["contacto"]  or "—",
            "nit":              r["nit"]        or "—",
            "telefono":         r["telefono"]   or "—",
            "correo":           r["correo"]     or "—",
            "direccion":        r["direccion"]  or "—",
            "activo":           r["activo"],
            "fecha_creacion":   r["fecha_creacion"].strftime("%Y-%m-%d %H:%M") if r["fecha_creacion"] else "—",
            "creado_por":       r["creado_por"] or "—",
        }
        for r in rows
    ]


def get_proveedor_by_id(id_proveedor):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """SELECT id_proveedor, codigo_proveedor, nombre, contacto,
                          nit, telefono, correo, direccion, activo
                   FROM proveedor WHERE id_proveedor = %s""",
                (id_proveedor,)
            )
            row = cur.fetchone()
    return dict(row) if row else None


def get_proveedor_by_codigo(codigo_proveedor):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """SELECT id_proveedor, codigo_proveedor, nombre, contacto,
                          nit, telefono, correo, direccion, activo
                   FROM proveedor WHERE codigo_proveedor ILIKE %s""",
                (f"%{codigo_proveedor.strip()}%",)
            )
            row = cur.fetchone()
    return dict(row) if row else None


def insert_proveedor(nombre, contacto, nit, telefono, correo,
                     direccion, activo, id_usuario_creacion):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO proveedor
                   (nombre, contacto, nit, telefono, correo,
                    direccion, activo, id_usuario_creacion)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (nombre, contacto, nit, telefono, correo,
                 direccion, activo, id_usuario_creacion)
            )
        conn.commit()


def update_proveedor(id_proveedor, nombre, contacto, nit, telefono,
                     correo, direccion, activo):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE proveedor
                   SET nombre=%s, contacto=%s, nit=%s, telefono=%s,
                       correo=%s, direccion=%s, activo=%s
                   WHERE id_proveedor=%s""",
                (nombre, contacto, nit, telefono, correo,
                 direccion, activo, id_proveedor)
            )
        conn.commit()

# ------------------------------------------------------------
# Insumos
# ------------------------------------------------------------

def get_unidades_medida_insumo():
    return get_unidades_medida()

def get_insumos(busqueda="", estado="todos"):
    condiciones = []
    parametros = []
    busqueda = busqueda.strip()
    if busqueda:
        condiciones.append("(i.nombre ILIKE %s OR i.codigo_insumo ILIKE %s)")
        parametros.extend([f"%{busqueda}%", f"%{busqueda}%"])
    if estado == "activos":
        condiciones.append("i.activo = TRUE")
    elif estado == "inactivos":
        condiciones.append("i.activo = FALSE")
    where_sql = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""
    query = f"""
        SELECT i.id_insumo, i.codigo_insumo, i.nombre, i.descripcion,
               u.nombre AS unidad, i.costo, i.activo,
               i.fecha_creacion, us.nombre_completo AS creado_por
        FROM insumo i
        LEFT JOIN unidad_medida u  ON i.id_unidad_medida = u.id_unidad
        LEFT JOIN usuarios     us  ON i.id_usuario_creacion = us.id_usuario
        {where_sql}
        ORDER BY i.id_insumo DESC
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, parametros)
            rows = cur.fetchall()
    return [
        {
            "id_insumo":      r["id_insumo"],
            "codigo_insumo":  r["codigo_insumo"],
            "nombre":         r["nombre"],
            "descripcion":    r["descripcion"] or "—",
            "unidad":         r["unidad"]      or "—",
            "costo":          r["costo"],
            "activo":         r["activo"],
            "fecha_creacion": r["fecha_creacion"].strftime("%Y-%m-%d %H:%M") if r["fecha_creacion"] else "—",
            "creado_por":     r["creado_por"]  or "—",
        }
        for r in rows
    ]


def get_insumo_by_id(id_insumo):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """SELECT id_insumo, codigo_insumo, nombre, descripcion,
                          id_unidad_medida, costo, activo
                   FROM insumo WHERE id_insumo = %s""",
                (id_insumo,)
            )
            row = cur.fetchone()
    return dict(row) if row else None


def get_insumo_by_codigo(codigo_insumo):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """SELECT id_insumo, codigo_insumo, nombre, descripcion,
                          id_unidad_medida, costo, activo
                   FROM insumo WHERE codigo_insumo ILIKE %s""",
                (f"%{codigo_insumo.strip()}%",)
            )
            row = cur.fetchone()
    return dict(row) if row else None


def insert_insumo(nombre, descripcion, id_unidad_medida, costo,
                  activo, id_usuario_creacion):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO insumo
                   (nombre, descripcion, id_unidad_medida, costo,
                    activo, id_usuario_creacion)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (nombre, descripcion, id_unidad_medida, costo,
                 activo, id_usuario_creacion)
            )
        conn.commit()


def update_insumo(id_insumo, nombre, descripcion, id_unidad_medida,
                  costo, activo):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE insumo
                   SET nombre=%s, descripcion=%s, id_unidad_medida=%s,
                       costo=%s, activo=%s
                   WHERE id_insumo=%s""",
                (nombre, descripcion, id_unidad_medida, costo,
                 activo, id_insumo)
            )
        conn.commit()

# ------------------------------------------------------------
# Ventas
# ------------------------------------------------------------
 
def get_productos_activos():
    """Lista reducida de productos activos para el selectbox de ventas."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """SELECT id_producto, codigo_producto, nombre, precio
                   FROM producto WHERE activo = TRUE
                   ORDER BY nombre"""
            )
            rows = cur.fetchall()
    return [dict(r) for r in rows]
 
 
def insert_venta(fecha, id_cliente, id_usuario, lineas):
    """Inserta la cabecera, el detalle y los movimientos de Kardex
    en una sola transacción. Devuelve el id_venta generado."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO venta_cabecera (fecha_venta, id_cliente, id_usuario)
                   VALUES (%s, %s, %s) RETURNING id_venta""",
                (fecha, id_cliente, id_usuario)
            )
            id_venta = cur.fetchone()[0]
 
            for linea in lineas:
                cur.execute(
                    """INSERT INTO venta_detalle
                       (id_venta, id_producto, cantidad, precio_unitario)
                       VALUES (%s, %s, %s, %s)""",
                    (id_venta, linea["id_producto"],
                     linea["cantidad"], linea["precio"])
                )
                cur.execute(
                    """INSERT INTO movimiento_inventario
                       (id_producto, tipo_movimiento, cantidad,
                        referencia_tipo, referencia_id, id_usuario_creacion)
                       VALUES (%s, 'salida_venta', %s, 'venta', %s, %s)""",
                    (linea["id_producto"], linea["cantidad"],
                     id_venta, id_usuario)
                )
        conn.commit()
    return id_venta
 
 
def get_venta_codigo(id_venta):
    """Devuelve el codigo_venta generado para mostrar en el mensaje de éxito."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT codigo_venta FROM venta_cabecera WHERE id_venta = %s",
                (id_venta,)
            )
            row = cur.fetchone()
    return row["codigo_venta"] if row else ""
 
 
def get_ventas(fecha_desde, fecha_hasta, busqueda=""):
    """Ventas en un rango de fechas, con filtro opcional por código o cliente."""
    condiciones = ["v.fecha_venta BETWEEN %s AND %s"]
    parametros = [fecha_desde, fecha_hasta]
 
    busqueda = busqueda.strip()
    if busqueda:
        condiciones.append(
            "(v.codigo_venta ILIKE %s OR c.nombre ILIKE %s)"
        )
        parametros.extend([f"%{busqueda}%", f"%{busqueda}%"])
 
    where_sql = "WHERE " + " AND ".join(condiciones)
 
    query = f"""
        SELECT
            v.id_venta,
            v.codigo_venta,
            v.fecha_venta,
            COALESCE(c.nombre, 'Consumidor Final') AS nombre_cliente,
            SUM(d.cantidad * d.precio_unitario)     AS total,
            us.nombre_completo                      AS registrado_por
        FROM venta_cabecera v
        LEFT JOIN cliente       c  ON v.id_cliente = c.id_cliente
        LEFT JOIN venta_detalle d  ON v.id_venta   = d.id_venta
        LEFT JOIN usuarios      us ON v.id_usuario  = us.id_usuario
        {where_sql}
        GROUP BY v.id_venta, v.codigo_venta, v.fecha_venta,
                 c.nombre, us.nombre_completo
        ORDER BY v.id_venta DESC
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, parametros)
            rows = cur.fetchall()
 
    return [
        {
            "id_venta":       r["id_venta"],
            "codigo_venta":   r["codigo_venta"],
            "fecha_venta":    str(r["fecha_venta"]),
            "nombre_cliente": r["nombre_cliente"],
            "total":          float(r["total"] or 0),
            "registrado_por": r["registrado_por"] or "—",
        }
        for r in rows
    ]