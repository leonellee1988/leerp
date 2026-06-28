import streamlit as st
import pandas as pd
import db

def _formulario(datos, form_key):
    with st.form(f"form_proveedor_{form_key}"):
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre / Razón social",
                                   value=datos["nombre"] if datos else "",
                                   placeholder="Ej. Distribuidora La Central")
        with col2:
            contacto = st.text_input("Nombre del contacto",
                                     value=datos["contacto"] if datos else "",
                                     placeholder="Ej. María López")

        col3, col4 = st.columns(2)
        with col3:
            nit = st.text_input("NIT",
                                value=datos["nit"] if datos else "",
                                placeholder="Ej. 1234567-8")
        with col4:
            telefono = st.text_input("Teléfono",
                                     value=datos["telefono"] if datos else "",
                                     placeholder="Ej. 2234-5678")

        col5, col6 = st.columns(2)
        with col5:
            correo = st.text_input("Correo electrónico",
                                   value=datos["correo"] if datos else "",
                                   placeholder="Ej. ventas@proveedor.com")
        with col6:
            direccion = st.text_input("Dirección",
                                      value=datos["direccion"] if datos else "",
                                      placeholder="Dirección del proveedor")

        activo = st.checkbox("Proveedor activo", value=datos["activo"] if datos else True)

        _, col_g, _ = st.columns([2, 3, 2])
        with col_g:
            guardar = st.form_submit_button("Guardar proveedor", type="primary",
                                            use_container_width=True)

    return guardar, nombre, contacto, nit, telefono, correo, direccion, activo


def mostrar():
    usuario = st.session_state.usuario_actual

    if st.session_state.get("modulo_anterior") != "proveedores":
        st.session_state.proveedor_vista = "nuevo"
        st.session_state.proveedor_editando = None
    st.session_state.modulo_anterior = "proveedores"

    for k, v in [("proveedor_editando", None), ("proveedor_form_key", 0),
                 ("proveedor_mensaje", None), ("proveedor_vista", "nuevo")]:
        if k not in st.session_state:
            st.session_state[k] = v

    st.title("Proveedores")
    st.caption("Registro de proveedores activos e inactivos")

    if st.session_state.proveedor_mensaje:
        st.success(st.session_state.proveedor_mensaje)
        st.session_state.proveedor_mensaje = None

    col_b1, col_b2, col_b3, col_esp = st.columns([1.4, 1.4, 1.4, 4.8])
    for col, vista, label in [
        (col_b1, "nuevo", "Nuevo registro"),
        (col_b2, "consultar", "Consultar"),
        (col_b3, "modificar", "Modificar"),
    ]:
        with col:
            t = "primary" if st.session_state.proveedor_vista == vista else "secondary"
            if st.button(label, key=f"vista_prv_{vista}", type=t, use_container_width=True):
                st.session_state.proveedor_vista = vista
                st.session_state.proveedor_editando = None
                st.rerun()

    st.divider()

    # ===========================================================
    # VISTA: Nuevo registro
    # ===========================================================
    if st.session_state.proveedor_vista == "nuevo":

        guardar, nombre, contacto, nit, telefono, correo, direccion, activo = \
            _formulario(None, st.session_state.proveedor_form_key)

        st.caption("Se registra automáticamente quién creó este proveedor y la fecha de alta.")

        if guardar:
            if not nombre.strip():
                st.error("El nombre es obligatorio.")
            else:
                db.insert_proveedor(
                    nombre.strip(), contacto.strip(), nit.strip(),
                    telefono.strip(), correo.strip(), direccion.strip(),
                    activo, usuario["id_usuario"]
                )
                recientes = db.get_proveedores(busqueda=nombre.strip())
                codigo = recientes[0]["codigo_proveedor"] if recientes else ""
                st.session_state.proveedor_mensaje = f"Proveedor {codigo} — '{nombre.strip()}' guardado correctamente."
                st.session_state.proveedor_form_key += 1
                st.rerun()

    # ===========================================================
    # VISTA: Consultar
    # ===========================================================
    elif st.session_state.proveedor_vista == "consultar":

        col_busqueda, col_estado, col_buscar = st.columns([2.5, 1.5, 0.7])
        with col_busqueda:
            busqueda = st.text_input("Buscar por nombre, NIT o código",
                                     key="busqueda_proveedores",
                                     placeholder="Ej. Distribuidora o PRV-0003")
        with col_estado:
            estado_filtro = st.selectbox("Estado", ["Todos", "Activos", "Inactivos"],
                                         key="estado_filtro_proveedores")
        with col_buscar:
            st.markdown("<div style='padding-top:28px;'>", unsafe_allow_html=True)
            buscar = st.button("Buscar", type="primary", use_container_width=True,
                               key="btn_buscar_proveedores")
            st.markdown("</div>", unsafe_allow_html=True)

        estado_map = {"Todos": "todos", "Activos": "activos", "Inactivos": "inactivos"}

        if not buscar:
            st.info("Configura los filtros y presiona Buscar.")
        else:
            lista = db.get_proveedores(busqueda=busqueda,
                                       estado=estado_map[estado_filtro])
            if not lista:
                st.info("No hay proveedores que coincidan con la búsqueda.")
            else:
                st.caption(f"Mostrando {len(lista)} proveedor(es)")
                df = pd.DataFrame([{
                    "ID":            p["codigo_proveedor"],
                    "Nombre":        p["nombre"],
                    "Contacto":      p["contacto"],
                    "NIT":           p["nit"],
                    "Teléfono":      p["telefono"],
                    "Correo":        p["correo"],
                    "Dirección":     p["direccion"],
                    "Estado":        "Activo" if p["activo"] else "Inactivo",
                    "Creado por":    p["creado_por"],
                    "Fecha creación":p["fecha_creacion"],
                } for p in lista])
                st.dataframe(df, use_container_width=True, hide_index=True)

    # ===========================================================
    # VISTA: Modificar
    # ===========================================================
    elif st.session_state.proveedor_vista == "modificar":

        st.subheader("Buscar proveedor a modificar")
        col_buscar, col_btn = st.columns([4, 1])
        with col_buscar:
            termino = st.text_input("Código del proveedor",
                                    placeholder="Ej. PRV-0003")
        with col_btn:
            st.markdown("<div style='padding-top:28px;'>", unsafe_allow_html=True)
            buscar_mod = st.button("Buscar", type="primary",
                                   use_container_width=True, key="btn_buscar_prv_mod")
            st.markdown("</div>", unsafe_allow_html=True)

        if buscar_mod and termino.strip():
            resultado = db.get_proveedor_by_codigo(termino.strip())
            if not resultado:
                st.session_state.proveedor_editando = None
                st.warning("No se encontró ningún proveedor con ese código. Verifica e intenta de nuevo (ej. PRV-0003).")
            else:
                st.session_state.proveedor_editando = resultado["id_proveedor"]
                st.rerun()

        if st.session_state.proveedor_editando:
            datos = db.get_proveedor_by_id(st.session_state.proveedor_editando)
            if datos:
                st.divider()
                st.caption(f"Editando: **{datos['codigo_proveedor']}** — {datos['nombre']}")

                guardar, nombre, contacto, nit, telefono, correo, direccion, activo = \
                    _formulario(datos, st.session_state.proveedor_form_key)

                if guardar:
                    if not nombre.strip():
                        st.error("El nombre es obligatorio.")
                    else:
                        db.update_proveedor(
                            st.session_state.proveedor_editando,
                            nombre.strip(), contacto.strip(), nit.strip(),
                            telefono.strip(), correo.strip(), direccion.strip(), activo
                        )
                        datos_act = db.get_proveedor_by_id(st.session_state.proveedor_editando)
                        codigo = datos_act["codigo_proveedor"] if datos_act else ""
                        st.session_state.proveedor_mensaje = f"Proveedor {codigo} — '{nombre.strip()}' actualizado correctamente."
                        st.session_state.proveedor_editando = None
                        st.session_state.proveedor_form_key += 1
                        st.rerun()