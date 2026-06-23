# main.py
# Punto de entrada de LEERP — login, navegación y enrutamiento de módulos.
#
# Reemplaza al main.py mínimo de prueba. A partir de aquí, cada módulo
# nuevo (productos.py, clientes.py, etc.) se agrega en el diccionario
# MODULOS, abajo, siguiendo el mismo patrón.

import streamlit as st

import auth
import db
from utils import permisos
from utils.navegacion import NAV_STRUCTURE, COLOR_GRUPO
from utils.iconos import get_icono
from pages import productos

st.set_page_config(
    page_title="LEERP",
    page_icon="app/assets/leerp-icon.ico",
    layout="wide",
)

# ------------------------------------------------------------
# Estilos globales (fuera del login) — la mayoría del color ya lo
# resuelve .streamlit/config.toml ([theme]). Aquí solo lo que el tema
# no cubre: ocultar el menú automático y forzar contraste de texto
# dentro del sidebar oscuro (mismo aprendizaje del login: el texto
# necesita color explícito, no se puede asumir que el tema lo resuelve).
# ------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@700&family=Inter:wght@400;500;600&display=swap');

[data-testid="stSidebarNav"] { display: none; }

[data-testid="stSidebar"] h3 {
    font-family: 'Sora', sans-serif !important;
    font-weight: 700 !important;
}
[data-testid="stSidebarContent"] * {
    color: #E5EEF5 !important;
}
[data-testid="stSidebar"] button[kind="secondary"] {
    background-color: transparent !important;
    border: none !important;
    color: #C7D6E5 !important;
    justify-content: flex-start !important;
}
[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] {
    justify-content: flex-start !important;
}
[data-testid="stSidebar"] button div[class*="e12tamyi2"] {
    justify-content: flex-start !important;
    width: 100% !important;
}

[data-testid="stSidebar"] .stCaption {
    color: #5B7FA0 !important;
    letter-spacing: 1px;
    font-size: 11px !important;
    text-transform: uppercase;
}
[data-testid="stSidebarContent"] {
    padding-top: 1rem !important;
}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
    gap: 0.3rem !important;
}
[data-testid="stSidebar"] hr {
    margin: 1rem 0 !important;
    border-color: rgba(255,255,255,0.15) !important;
}
.block-container {
    padding-top: 2rem;
    font-family: 'Inter', sans-serif !important;
}
.block-container h1, .block-container h2, .block-container h3 {
    font-family: 'Sora', sans-serif !important;
}
.leerp-sidebar-logo svg { width: 26px !important; height: 26px !important; }
.leerp-sidebar-logo { margin-bottom: 6px; }
.st-key-btn_logout, .st-key-btn_logout button {
    border: 1px solid #3A7CA5 !important;
    background-color: transparent !important;
    color: #C7D6E5 !important;
}
.st-key-btn_logout button:hover {
    border-color: #00C2A8 !important;
    color: #FFFFFF !important;
}
            
[data-testid="stSidebar"] hr:first-of-type {
    margin-bottom: 2rem !important;
}

/* Color de texto, cursor y placeholder para todos los inputs de módulos.
   caret-color fuerza el cursor parpadeante a blanco sobre fondo navy.
   placeholder en blanco semitransparente evita que compita con el valor real. */
.stTextInput > div > div > input,
.stTextArea textarea,
.stNumberInput input,
.stSelectbox div[data-baseweb="select"] div {
    color: #FFFFFF !important;
    caret-color: #FFFFFF !important;
}

.stTextInput > div > div > input::placeholder,
.stTextArea textarea::placeholder,
.stNumberInput input::placeholder {
    color: rgba(255, 255, 255, 0.4) !important;
}
            
/* Botón Editar en tabla — mismo estilo que botón Ingresar del login */
[class*="st-key-editar_producto"] button {
    background-color: #00C2A8 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 11px !important;
    font-weight: 600 !important;
}
[class*="st-key-editar_producto"] button:hover {
    background-color: #0A2540 !important;
    color: #FFFFFF !important;
}

</style>
""", unsafe_allow_html=True)

auth.inicializar_sesion()

if not auth.usuario_autenticado():
    auth.mostrar_login()
    st.stop()

usuario = st.session_state.usuario_actual
rol = usuario["rol"]

if "pagina_actual" not in st.session_state:
    st.session_state.pagina_actual = "inicio"


def menu_visible(rol):
    """Filtra NAV_STRUCTURE según los permisos del rol. 'inicio' siempre
    es visible; los grupos que se quedan sin items se omiten por completo."""
    menu = []
    for grupo in NAV_STRUCTURE:
        items = [
            item for item in grupo["items"]
            if item.get("siempre_visible") or permisos.tiene_permiso(rol, item["key"])
        ]
        if items:
            menu.append({"grupo": grupo["grupo"], "items": items})
    return menu


# ------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------
with st.sidebar:
    st.markdown(
        f'<div class="leerp-sidebar-logo" style="display:flex; align-items:center; gap:8px;">'
        f'{auth.LEERP_ICON_SVG}'
        f'<span style="font-family:\'Sora\',sans-serif; font-weight:700; font-size:18px; color:#FFFFFF;">LEERP</span>'
        f'</div>',
        unsafe_allow_html=True
    )
    st.caption("GESTIÓN INTELIGENTE · MIPYMES")
    st.divider()

    for grupo in menu_visible(rol):
        if grupo["grupo"]:
            st.caption(grupo["grupo"])
        for item in grupo["items"]:
            activo = st.session_state.pagina_actual == item["key"]
            col_icono, col_boton = st.columns([1, 9], gap="small")
            with col_icono:
                st.markdown(
                    f'<div style="padding-top:8px;">{get_icono(item["key"])}</div>',
                    unsafe_allow_html=True
                )
            with col_boton:
                if st.button(
                    item["label"],
                    key=f"nav_{item['key']}",
                    type="primary" if activo else "secondary",
                    use_container_width=True,
                ):
                    st.session_state.pagina_actual = item["key"]
                    st.rerun()
        st.write("")
    st.divider()

    partes_nombre = usuario["nombre"].split()
    iniciales = (partes_nombre[0][0] + partes_nombre[-1][0]).upper() if len(partes_nombre) > 1 else partes_nombre[0][0].upper()

    st.markdown(
        f'''
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:30px;">
            <div style="width:30px; height:30px; border-radius:50%; background:#00C2A8;
                        display:flex; align-items:center; justify-content:center;
                        font-size:12px; font-weight:600; color:#0A2540; flex-shrink:0;">
                {iniciales}
            </div>
            <div>
                <div style="font-size:13px; color:#FFFFFF; font-weight:500;">{usuario['nombre']}</div>
                <div style="font-size:11px; color:#5B7FA0;">{rol}</div>
            </div>
        </div>
        ''',
        unsafe_allow_html=True
    )

    _, col_centro, _ = st.columns([1, 2, 1])
    with col_centro:
        if st.button("Cerrar sesión", key="btn_logout"):
            auth.cerrar_sesion()


# ------------------------------------------------------------
# Pantalla de inicio (home)
# ------------------------------------------------------------

def mostrar_inicio():
    config = db.get_config_empresa()
    nombre_empresa = config["nombre_empresa"] if config else "tu empresa"

    st.title(f"Bienvenido, {usuario['nombre']}")
    st.caption(f"{nombre_empresa} — Gestión simple para decisiones inteligentes.")
    st.write("")

    items_home = [
        (grupo["grupo"], item)
        for grupo in menu_visible(rol) for item in grupo["items"]
        if item["key"] != "inicio"
    ]

    cols = st.columns(4)
    for i, (grupo_nombre, item) in enumerate(items_home):
        colores = COLOR_GRUPO.get(grupo_nombre, {"bg": "#EEF2F6", "icon": "#5B7280"})
        with cols[i % 4]:
            with st.container(border=True):
                st.markdown(
                    f'<div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">'
                    f'<div style="width:32px; height:32px; border-radius:8px; background:{colores["bg"]}; '
                    f'display:flex; align-items:center; justify-content:center; flex-shrink:0;">'
                    f'<span style="color:{colores["icon"]}; display:flex;">{get_icono(item["key"])}</span>'
                    f'</div>'
                    f'<strong style="color:#0A2540;">{item["label"]}</strong>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                if st.button("Abrir", key=f"home_{item['key']}", use_container_width=True):
                    st.session_state.pagina_actual = item["key"]
                    st.rerun()

# ------------------------------------------------------------
# Enrutamiento de módulos
# ------------------------------------------------------------
# Los módulos reales se van agregando aquí a medida que se construyen.
# Mientras un módulo no exista en este diccionario, se muestra un
# placeholder "en construcción" en vez de fallar.

MODULOS = {
    "inicio": mostrar_inicio,
    "productos": productos.mostrar,
}

pagina = st.session_state.pagina_actual

# Seguridad: antes solo ocultábamos los módulos sin permiso del menú, pero
# si "pagina_actual" quedaba en ese valor por sesión previa (ej. cambiaron
# de rol, o quedó guardado en el navegador), igual se renderizaba. Ahora
# se valida también aquí, no solo al construir el sidebar.
acceso_permitido = pagina == "inicio" or permisos.tiene_permiso(rol, pagina)

if not acceso_permitido:
    st.warning("No tienes acceso a ese módulo. Te llevamos a Inicio.")
    st.session_state.pagina_actual = "inicio"
    st.rerun()
elif pagina in MODULOS:
    MODULOS[pagina]()
else:
    etiqueta = pagina.capitalize()
    for grupo in NAV_STRUCTURE:
        for item in grupo["items"]:
            if item["key"] == pagina:
                etiqueta = item["label"]
    st.title(etiqueta)
    st.info("Este módulo todavía no está construido — próxima sesión.")