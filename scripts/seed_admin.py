# seed_admin.py
# Bootstrap: crea el primer usuario admin en una instancia nueva de LEERP.
# Se corre UNA SOLA VEZ por cliente, justo después de aplicar
# sql/leerp_schema.sql en su proyecto Neon — antes de esto no existe
# ningún usuario con el cual iniciar sesión.
#
# Uso:
#   python scripts/seed_admin.py

import getpass
import os
import sys

import psycopg2
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "app", "utils"))
from auth_utils import hash_password  # noqa: E402

load_dotenv()


def get_connection():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.environ.get("DB_PORT", 5432),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        sslmode=os.environ.get("DB_SSLMODE", "require"),
    )


def main():
    print("=== LEERP — creación del primer usuario admin ===")
    nombre_completo = input("Nombre completo: ").strip()
    usuario = input("Usuario (login): ").strip()
    password = getpass.getpass("Contraseña: ")
    password_confirm = getpass.getpass("Confirmar contraseña: ")

    if password != password_confirm:
        print("Las contraseñas no coinciden. Abortado.")
        return

    password_hash = hash_password(password)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO usuarios (nombre_completo, usuario, password_hash, rol) "
                "VALUES (%s, %s, %s, 'admin')",
                (nombre_completo, usuario, password_hash),
            )
        conn.commit()

    print(f"Usuario admin '{usuario}' creado correctamente.")


if __name__ == "__main__":
    main()