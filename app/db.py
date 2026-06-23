# db.py
# Capa de datos — conexión a PostgreSQL (Neon) y queries.
#
# Cada módulo (productos.py, clientes.py, ventas.py, etc.) llama a
# estas funciones, nunca abre su propia conexión directamente — así,
# si algo de la conexión cambia, solo se toca este archivo.
#
# Por ahora solo incluye lo necesario para el login. Las funciones de
# cada módulo (get_productos, insert_producto, etc.) se van agregando
# aquí abajo a medida que se construye cada página, siguiendo siempre
# el mismo patrón: with get_connection() as conn: ... con parámetros
# seguros (%s), nunca armando el SQL con f-strings.

import os

import psycopg2
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
        with conn.cursor() as cur:
            cur.execute(
                "SELECT nombre_empresa, pais, moneda_codigo, moneda_simbolo, logo_url "
                "FROM config_empresa LIMIT 1"
            )
            row = cur.fetchone()

    if not row:
        return None
    return {
        "nombre_empresa": row[0],
        "pais": row[1],
        "moneda_codigo": row[2],
        "moneda_simbolo": row[3],
        "logo_url": row[4],
    }


# ------------------------------------------------------------
# Catálogos (usados por varios módulos, no solo Productos)
# ------------------------------------------------------------

def get_categorias():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id_categoria, nombre FROM categoria WHERE activo = TRUE ORDER BY nombre")
            rows = cur.fetchall()
    return [{"id_categoria": r[0], "nombre": r[1]} for r in rows]


def get_unidades_medida():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id_unidad, nombre FROM unidad_medida ORDER BY nombre")
            rows = cur.fetchall()
    return [{"id_unidad": r[0], "nombre": r[1]} for r in rows]


# ------------------------------------------------------------
# Productos
# ------------------------------------------------------------

def get_productos(busqueda="", id_categoria=None, estado="todos"):
    """Lista de productos para la pantalla de Consultar, con filtros opcionales.
    'busqueda' acepta nombre parcial o el código exacto/parcial (ej. 'PRD-0042')."""
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
        SELECT p.id_producto, p.codigo_producto, p.nombre, c.nombre, u.nombre, p.precio, p.activo
        FROM producto p
        LEFT JOIN categoria c ON p.id_categoria = c.id_categoria
        LEFT JOIN unidad_medida u ON p.id_unidad_medida = u.id_unidad
        {where_sql}
        ORDER BY p.id_producto DESC
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, parametros)
            rows = cur.fetchall()

    return [
        {
            "id_producto": r[0], "codigo_producto": r[1], "nombre": r[2], "categoria": r[3] or "—",
            "unidad": r[4] or "—", "precio": r[5], "activo": r[6],
        }
        for r in rows
    ]


def get_producto_by_id(id_producto):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id_producto, codigo_producto, nombre, descripcion, tipo, id_categoria, "
                "id_unidad_medida, costo, precio, activo "
                "FROM producto WHERE id_producto = %s",
                (id_producto,)
            )
            row = cur.fetchone()
    if not row:
        return None
    return {
        "id_producto": row[0], "codigo_producto": row[1], "nombre": row[2], "descripcion": row[3],
        "tipo": row[4], "id_categoria": row[5], "id_unidad_medida": row[6],
        "costo": row[7], "precio": row[8], "activo": row[9],
    }


def insert_producto(nombre, descripcion, tipo, id_categoria, id_unidad_medida,
                     costo, precio, activo, id_usuario_creacion):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO producto "
                "(nombre, descripcion, tipo, id_categoria, id_unidad_medida, "
                "costo, precio, activo, id_usuario_creacion) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (nombre, descripcion, tipo, id_categoria, id_unidad_medida,
                 costo, precio, activo, id_usuario_creacion)
            )
        conn.commit()


def update_producto(id_producto, nombre, descripcion, tipo, id_categoria,
                     id_unidad_medida, costo, precio, activo):
    """Actualiza un producto existente.
    costo y precio son campos distintos — costo es el costo de adquisición,
    precio es el precio de venta al cliente. No mezclarlos."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE producto SET nombre=%s, descripcion=%s, tipo=%s, "
                "id_categoria=%s, id_unidad_medida=%s, costo=%s, precio=%s, activo=%s "
                "WHERE id_producto=%s",
                (nombre, descripcion, tipo, id_categoria, id_unidad_medida,
                 costo, precio, activo, id_producto)
            )
        conn.commit()