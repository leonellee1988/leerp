# auth.py
# Pantalla de login con identidad de marca LEERP + manejo de sesión
#
# Requiere en la BD:
#   - tabla "usuarios"        (login + rol)
#   - tabla "config_empresa"  (nombre del cliente, logo opcional)
#
# Requiere en db.py las funciones: verificar_login(), get_config_empresa()
# (ver snippet aparte para pegar en tu db.py)
#
# Uso desde main.py:
#
#   import auth
#   auth.inicializar_sesion()
#   if not auth.usuario_autenticado():
#       auth.mostrar_login()
#       st.stop()
#   # ... resto de tu main.py actual ...

import streamlit as st
import db

# Ícono LEERP — mismo SVG de la identidad de marca, embebido para no
# depender de un archivo de imagen externo.
LEERP_ICON_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 56 56" width="44" height="44">
  <rect width="56" height="56" rx="12" fill="#0A2540"/>
  <rect x="10" y="10" width="16" height="16" rx="4" fill="#00C2A8"/>
  <rect x="30" y="10" width="16" height="16" rx="4" fill="#00C2A8"/>
  <rect x="10" y="30" width="16" height="16" rx="4" fill="#00C2A8"/>
  <rect x="30" y="30" width="16" height="16" rx="4" fill="#00C2A8" opacity="0.32"/>
</svg>
"""

# Nota: los selectores data-testid de Streamlit cambian entre versiones.
# Si algún estilo no se aplica, inspecciona el elemento con el navegador
# (F12) y ajustamos el selector exacto a tu versión instalada.
ESTILOS_LOGIN = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@600;700&family=Inter:wght@400;500;600&display=swap');

.stApp {
    background: #0A2540;
}

.block-container {
    padding-top: 4.5rem;
}

/* Oculta el menú automático de páginas de Streamlit — la navegación
   real la construye main.py, no el listado autodetectado de pages/ */
[data-testid*="Sidebar"] { display: none !important; }

.st-key-login_card {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 32px 36px 24px 36px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
}

.st-key-login_card { gap: 0.2rem !important; }
.st-key-login_card > div { margin: 0 !important; }

.login-icon-wrap { text-align: center; margin-bottom: 12px; }

.login-title {
    font-family: 'Sora', 'Inter', sans-serif;
    font-weight: 700;
    font-size: 28px;
    color: #0A2540;
    text-align: center;
    letter-spacing: -0.5px;
    margin: 0;
}

.login-tagline {
    font-family: 'Inter', sans-serif;
    font-size: 10px;
    font-weight: 500;
    color: #3A7CA5;
    text-align: center;
    letter-spacing: 1.4px;
    text-transform: uppercase;
    margin: 2px 0 20px 0;
}

.login-divider {
    border-top: 1px solid rgba(10, 37, 64, 0.1);
    margin: 4px 0 18px 0;
}

.login-empresa {
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    color: #5B7280;
    text-align: center;
    margin-bottom: 20px;
}
.login-empresa b { color: #0A2540; }

div[data-testid="stForm"] {
    border: none !important;
    padding: 0 !important;
    margin: 0 !important;
}

div[data-testid="stForm"] div[data-testid="stVerticalBlock"] { gap: 0.2rem !important; }

.stTextInput > div > div > input {
    border-radius: 8px;
    border: 1px solid #D0E4F0;
}
.stTextInput > div > div > input:focus {
    border-color: #00C2A8;
    box-shadow: 0 0 0 1px #00C2A8;
}

.stTextInput label {
    color: #0A2540 !important;
    font-family: 'Inter', sans-serif;
    font-weight: 500;
}

div[data-testid="stFormSubmitButton"] button {
    background-color: #00C2A8;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    width: 100%;
}

div[data-testid="stFormSubmitButton"] {
    margin-top: 12px;
}

div[data-testid="stFormSubmitButton"] button:hover {
    background-color: #0A2540;
    color: #FFFFFF;
}
</style>
"""


def inicializar_sesion():
    """Inicializa las claves de session_state usadas para el login."""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "usuario_actual" not in st.session_state:
        st.session_state.usuario_actual = None


def usuario_autenticado() -> bool:
    """True si hay una sesión activa."""
    inicializar_sesion()
    return st.session_state.logged_in


def mostrar_login():
    """Renderiza la pantalla de login. Llamar desde main.py cuando
    el usuario todavía no está autenticado."""
    inicializar_sesion()
    st.markdown(ESTILOS_LOGIN, unsafe_allow_html=True)

    config = db.get_config_empresa()
    nombre_empresa = config["nombre_empresa"] if config else "tu empresa"

    _, col, _ = st.columns([1, 1.1, 1])
    with col:
        with st.container(key="login_card"):
            st.markdown(
                f"""
                <div class="login-icon-wrap">{LEERP_ICON_SVG}</div>
                <p class="login-title">LEERP</p>
                <p class="login-tagline">GESTIÓN INTELIGENTE · MIPYMES</p>
                <div class="login-divider"></div>
                <p class="login-empresa">Ingresando a <b>{nombre_empresa}</b></p>
                """,
                unsafe_allow_html=True
            )

            with st.form("form_login"):
                usuario = st.text_input("Usuario")
                password = st.text_input("Contraseña", type="password")
                submitted = st.form_submit_button("Ingresar")

    if submitted:
        datos = db.verificar_login(usuario, password)
        if datos:
            st.session_state.logged_in = True
            st.session_state.usuario_actual = datos
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")


def cerrar_sesion():
    """Cierra la sesión actual y regresa a la pantalla de login."""
    st.session_state.logged_in = False
    st.session_state.usuario_actual = None
    st.rerun()