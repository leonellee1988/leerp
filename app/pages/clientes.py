import streamlit as st
import pandas as pd
import db

def _formulario(datos, form_key):
    with st.form(f"form_cliente_{form_key}"):
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre / Razón social",
                                   value=datos["nombre"] if datos else "",
                                   placeholder="Ej. Ferretería El Martillo")
        with col2:
            nit = st.text_input("NIT",
                                value=datos["nit"] if datos else "",
                                placeholder="Ej. 1234567-8")

        col3, col4 = st.columns(2)
        with col3:
            telefono = st.text_input("Teléfono",
                                     value=datos["telefono"] if datos else "",
                                     placeholder="Ej. 2234-5678")
        with col4:
            correo = st.text_input("Correo electrónico",
                                   value=datos["correo"] if datos else "",
                                   placeholder="Ej. contacto@empresa.com")

        direccion = st.text_area("Dirección",
                                 value=datos["direccion"] if datos else "",
                                 placeholder="Dirección completa del cliente")

        activo = st.checkbox("Cliente activo", value=datos["activo"] if datos else True)

        _, col_g, _ = st.columns([2, 3, 2])
        with col_g:
            guardar = st.form_submit_button("Guardar cliente", type="primary",
                                            use_container_width=True)

    return guardar, nombre, nit, telefono, correo, direccion, activo


def mostrar():
    usuario = st.session_state.usuario_actual

    if st.session_state.get("modulo_anterior") != "clientes":
        st.session_state.cliente_vista = "nuevo"
        st.session_state.cliente_editando = None
    st.session_state.modulo_anterior = "clientes"

    for k, v in [("cliente_editando", None), ("cliente_form_key", 0),
                 ("cliente_mensaje", None), ("cliente_vista", "nuevo")]:
        if k not in st.session_state:
            st.session_state[k] = v

    st.title("Clientes")
    st.caption("Cartera de clientes activos e inactivos")

    if st.session_state.cliente_mensaje:
        st.success(st.session_state.cliente_mensaje)
        st.session_state.cliente_mensaje = None

    col_b1, col_b2, col_b3, col_esp = st.columns([1.4, 1.4, 1.4, 4.8])
    for col, vista, label in [
        (col_b1, "nuevo", "Nuevo registro"),
        (col_b2, "consultar", "Consultar"),
        (col_b3, "modificar", "Modificar"),
    ]:
        with col:
            t = "primary" if st.session_state.cliente_vista == vista else "secondary"
            if st.button(label, key=f"vista_cli_{vista}", type=t, use_container_width=True):
                st.session_state.cliente_vista = vista
                st.session_state.cliente_editando = None
                st.rerun()

    st.divider()

    # ===========================================================
    # VISTA: Nuevo registro
    # ===========================================================
    if st.session_state.cliente_vista == "nuevo":

        guardar, nombre, nit, telefono, correo, direccion, activo = \
            _formulario(None, st.session_state.cliente_form_key)

        st.caption("Se registra automáticamente quién creó este cliente y la fecha de alta.")

        if guardar:
            if not nombre.strip():
                st.error("El nombre es obligatorio.")
            else:
                db.insert_cliente(
                    nombre.strip(), nit.strip(), telefono.strip(),
                    correo.strip(), direccion.strip(), activo,
                    usuario["id_usuario"]
                )
                recientes = db.get_clientes(busqueda=nombre.strip())
                codigo = recientes[0]["codigo_cliente"] if recientes else ""
                st.session_state.cliente_mensaje = f"Cliente {codigo} — '{nombre.strip()}' guardado correctamente."
                st.session_state.cliente_form_key += 1
                st.rerun()

    # ===========================================================
    # VISTA: Consultar
    # ===========================================================
    elif st.session_state.cliente_vista == "consultar":

        col_busqueda, col_estado, col_buscar = st.columns([2.5, 1.5, 0.7])
        with col_busqueda:
            busqueda = st.text_input("Buscar por nombre, NIT o código",
                                     key="busqueda_clientes",
                                     placeholder="Ej. Ferretería o CLI-0003")
        with col_estado:
            estado_filtro = st.selectbox("Estado", ["Todos", "Activos", "Inactivos"],
                                         key="estado_filtro_clientes")
        with col_buscar:
            st.markdown("<div style='padding-top:28px;'>", unsafe_allow_html=True)
            buscar = st.button("Buscar", type="primary", use_container_width=True,
                               key="btn_buscar_clientes")
            st.markdown("</div>", unsafe_allow_html=True)

        estado_map = {"Todos": "todos", "Activos": "activos", "Inactivos": "inactivos"}

        if not buscar:
            st.info("Configura los filtros y presiona Buscar.")
        else:
            lista = db.get_clientes(busqueda=busqueda,
                                    estado=estado_map[estado_filtro])
            if not lista:
                st.info("No hay clientes que coincidan con la búsqueda.")
            else:
                st.caption(f"Mostrando {len(lista)} cliente(s)")
                df = pd.DataFrame([{
                    "ID":            c["codigo_cliente"],
                    "Nombre":        c["nombre"],
                    "NIT":           c["nit"],
                    "Teléfono":      c["telefono"],
                    "Correo":        c["correo"],
                    "Dirección":     c["direccion"],
                    "Estado":        "Activo" if c["activo"] else "Inactivo",
                    "Creado por":    c["creado_por"],
                    "Fecha creación":c["fecha_creacion"],
                } for c in lista])
                st.dataframe(df, use_container_width=True, hide_index=True)

    # ===========================================================
    # VISTA: Modificar
    # ===========================================================
    elif st.session_state.cliente_vista == "modificar":

        st.subheader("Buscar cliente a modificar")
        col_buscar, col_btn = st.columns([4, 1])
        with col_buscar:
            termino = st.text_input("Código del cliente",
                                    placeholder="Ej. CLI-0003")
        with col_btn:
            st.markdown("<div style='padding-top:28px;'>", unsafe_allow_html=True)
            buscar_mod = st.button("Buscar", type="primary",
                                   use_container_width=True, key="btn_buscar_cli_mod")
            st.markdown("</div>", unsafe_allow_html=True)

        if buscar_mod and termino.strip():
            resultado = db.get_cliente_by_codigo(termino.strip())
            if not resultado:
                st.session_state.cliente_editando = None
                st.warning("No se encontró ningún cliente con ese código. Verifica e intenta de nuevo (ej. CLI-0003).")
            else:
                st.session_state.cliente_editando = resultado["id_cliente"]
                st.rerun()

        if st.session_state.cliente_editando:
            datos = db.get_cliente_by_id(st.session_state.cliente_editando)
            if datos:
                st.divider()
                st.caption(f"Editando: **{datos['codigo_cliente']}** — {datos['nombre']}")

                guardar, nombre, nit, telefono, correo, direccion, activo = \
                    _formulario(datos, st.session_state.cliente_form_key)

                if guardar:
                    if not nombre.strip():
                        st.error("El nombre es obligatorio.")
                    else:
                        db.update_cliente(
                            st.session_state.cliente_editando,
                            nombre.strip(), nit.strip(), telefono.strip(),
                            correo.strip(), direccion.strip(), activo
                        )
                        datos_act = db.get_cliente_by_id(st.session_state.cliente_editando)
                        codigo = datos_act["codigo_cliente"] if datos_act else ""
                        st.session_state.cliente_mensaje = f"Cliente {codigo} — '{nombre.strip()}' actualizado correctamente."
                        st.session_state.cliente_editando = None
                        st.session_state.cliente_form_key += 1
                        st.rerun()