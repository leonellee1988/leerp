# main.py
# Punto de entrada de LEERP — gate de login y navegación.
#
# Esta es una versión MÍNIMA, solo para confirmar que el login
# funciona de extremo a extremo. Los módulos reales (productos,
# clientes, ventas, etc.) se agregan después de esta prueba.

import streamlit as st
import auth

st.set_page_config(
    page_title="LEERP",
    page_icon="app/assets/leerp-icon.ico",
    layout="wide"
)

auth.inicializar_sesion()

if not auth.usuario_autenticado():
    auth.mostrar_login()
    st.stop()

# ------------------------------------------------------------
# A partir de aquí el usuario ya está autenticado.
# st.session_state.usuario_actual tiene: id_usuario, nombre, rol
# ------------------------------------------------------------

usuario = st.session_state.usuario_actual

with st.sidebar:
    st.write(f"👤 {usuario['nombre']}")
    st.caption(f"Rol: {usuario['rol']}")
    if st.button("Cerrar sesión"):
        auth.cerrar_sesion()

st.title("LEERP")
st.success(f"Bienvenido, {usuario['nombre']} — el login está funcionando correctamente.")