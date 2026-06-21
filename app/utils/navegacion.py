# navegacion.py
# Estructura del menú de LEERP, agrupado por sección.
#
# "inicio" siempre es visible para cualquier rol (siempre_visible=True).
# El resto de items se filtran en main.py contra permisos.py según el
# rol del usuario logueado.

NAV_STRUCTURE = [
    {
        "grupo": None,
        "items": [
            {"key": "inicio", "label": "Inicio", "siempre_visible": True},
        ],
    },
    {
        "grupo": "MAESTROS",
        "items": [
            {"key": "productos", "label": "Productos"},
            {"key": "clientes", "label": "Clientes"},
            {"key": "proveedores", "label": "Proveedores"},
            {"key": "insumos", "label": "Insumos"},
        ],
    },
    {
        "grupo": "TRANSACCIONES",
        "items": [
            {"key": "ventas", "label": "Ventas"},
            {"key": "compras", "label": "Compras"},
            {"key": "gastos", "label": "Gastos"},
        ],
    },
    {
        "grupo": "INVENTARIO",
        "items": [
            {"key": "inventarios", "label": "Inventarios"},
            {"key": "dashboard", "label": "Dashboard"},
        ],
    },
    {
        "grupo": "ADMINISTRACIÓN",
        "items": [
            {"key": "usuarios", "label": "Usuarios"},
            {"key": "configuracion", "label": "Configuración"},
        ],
    },
]

# Color del "chip" detrás del ícono en las tarjetas de inicio, por grupo.
# Si un grupo nuevo no está aquí, mostrar_inicio() usa un color gris neutro
# por defecto — no hace falta tocar esto al agregar módulos a un grupo
# existente, solo si se crea un grupo nuevo.
COLOR_GRUPO = {
    "MAESTROS": {"bg": "#E6F1FB", "icon": "#185FA5"},
    "TRANSACCIONES": {"bg": "#E1F5EE", "icon": "#0F6E56"},
    "INVENTARIO": {"bg": "#0A2540", "icon": "#7EB8D4"},
    "ADMINISTRACIÓN": {"bg": "#EAF4FA", "icon": "#3A7CA5"},
}