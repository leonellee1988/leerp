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