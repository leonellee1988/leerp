# permisos.py
# Matriz de permisos por rol — LEERP
#
# Roles:
#   admin     -> acceso total + gestión de usuarios y configuración
#   captura   -> solo ingreso de datos (maestros y transacciones)
#   analista  -> ingreso de datos + consultas/reportes
#   visor     -> solo consulta (dashboard, inventario), sin ingreso

PERMISOS = {
    "admin": {
        "productos", "clientes", "proveedores", "insumos",
        "ventas", "compras", "gastos",
        "inventarios", "dashboard_comercial", "dashboard_financiero",
        "usuarios", "configuracion",
    },
    "captura": {
        "productos", "clientes", "proveedores", "insumos",
        "ventas", "compras", "gastos",
    },
    "analista": {
        "productos", "clientes", "proveedores", "insumos",
        "ventas", "compras", "gastos",
        "inventarios", "dashboard_comercial", "dashboard_financiero",
    },
    "visor": {
        "inventarios", "dashboard_comercial", "dashboard_financiero",
    },
}


def tiene_permiso(rol: str, modulo: str) -> bool:
    """Valida si un rol puede acceder a un módulo específico."""
    return modulo in PERMISOS.get(rol, set())


def modulos_visibles(rol: str) -> set:
    """Devuelve el set de módulos que un rol puede ver en el menú lateral."""
    return PERMISOS.get(rol, set())