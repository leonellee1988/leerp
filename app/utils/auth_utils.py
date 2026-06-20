# auth_utils.py
# Funciones base de seguridad para LEERP.
# Requiere: pip install bcrypt
#
# Uso esperado dentro de db.py:
#   - al crear un usuario (solo admin): hash_password() antes de INSERT
#   - al hacer login: verificar_password() contra el hash guardado
#
# Nunca se compara ni se guarda la contraseña en texto plano.

import bcrypt


def hash_password(password: str) -> str:
    """Genera el hash bcrypt de una contraseña en texto plano."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_password(password: str, password_hash: str) -> bool:
    """Compara una contraseña en texto plano contra su hash guardado."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


# ------------------------------------------------------------
# Ejemplo de cómo se integrarían en db.py (patrón ya usado en
# Guatecompost: get_connection() + context manager + parámetros
# seguros con %s, equivalente al "?" de SQLite)
# ------------------------------------------------------------
#
# def insert_usuario(nombre_completo, usuario, password, rol="operador"):
#     password_hash = hash_password(password)
#     with get_connection() as conn:
#         with conn.cursor() as cur:
#             cur.execute(
#                 "INSERT INTO usuarios (nombre_completo, usuario, password_hash, rol) "
#                 "VALUES (%s, %s, %s, %s)",
#                 (nombre_completo, usuario, password_hash, rol)
#             )
#         conn.commit()
#
#
# def verificar_login(usuario, password):
#     with get_connection() as conn:
#         with conn.cursor() as cur:
#             cur.execute(
#                 "SELECT id_usuario, nombre_completo, password_hash, rol "
#                 "FROM usuarios WHERE usuario = %s AND activo = TRUE",
#                 (usuario,)
#             )
#             row = cur.fetchone()
#     if row and verificar_password(password, row[2]):
#         return {"id_usuario": row[0], "nombre": row[1], "rol": row[3]}
#     return None