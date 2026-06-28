import streamlit as st
import pandas as pd
import db

def _formulario(datos, opciones_unidad, simbolo, form_key):
    with st.form(f"form_insumo_{form_key}"):
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre",
                                   value=datos["nombre"] if datos else "",
                                   placeholder="Ej. Saco de abono 50kg")
        with col2:
            lista_u = list(opciones_unidad.keys()) or ["Sin unidades"]
            u_actual = next((n for n, i in opciones_unidad.items()
                             if datos and i == datos["id_unidad_medida"]), None)
            unidad_sel = st.selectbox("Unidad de medida", lista_u,
                                      index=lista_u.index(u_actual) if u_actual in lista_u else 0)

        col3, col4 = st.columns(2)
        with col3:
            costo = st.number_input(f"Costo ({simbolo})", min_value=0.0,
                                    value=round(float(datos["costo"]), 2) if datos else 0.0,
                                    step=0.5, format="%.2f")
        with col4:
            activo = st.checkbox("Insumo activo",
                                 value=datos["activo"] if datos else True)

        descripcion = st.text_area("Descripción (opcional)",
                                   value=(datos["descripcion"] or "") if datos else "",
                                   placeholder="Notas adicionales del insumo")

        _, col_g, _ = st.columns([2, 3, 2])
        with col_g:
            guardar = st.form_submit_button("Guardar insumo", type="primary",
                                            use_container_width=True)

    return guardar, nombre, unidad_sel, costo, activo, descripcion


def mostrar():
    usuario = st.session_state.usuario_actual

    if st.session_state.get("modulo_anterior") != "insumos":
        st.session_state.insumo_vista = "nuevo"
        st.session_state.insumo_editando = None
    st.session_state.modulo_anterior = "insumos"

    for k, v in [("insumo_editando", None), ("insumo_form_key", 0),
                 ("insumo_mensaje", None), ("insumo_vista", "nuevo")]:
        if k not in st.session_state:
            st.session_state[k] = v

    st.title("Insumos")
    st.caption("Catálogo de insumos y materiales")

    if st.session_state.insumo_mensaje:
        st.success(st.session_state.insumo_mensaje)
        st.session_state.insumo_mensaje = None

    unidades = db.get_unidades_medida()
    config = db.get_config_empresa()
    simbolo = config["moneda_simbolo"] if config else "$"
    opciones_unidad = {u["nombre"]: u["id_unidad"] for u in unidades}

    col_b1, col_b2, col_b3, col_esp = st.columns([1.4, 1.4, 1.4, 4.8])
    for col, vista, label in [
        (col_b1, "nuevo", "Nuevo registro"),
        (col_b2, "consultar", "Consultar"),
        (col_b3, "modificar", "Modificar"),
    ]:
        with col:
            t = "primary" if st.session_state.insumo_vista == vista else "secondary"
            if st.button(label, key=f"vista_ins_{vista}", type=t, use_container_width=True):
                st.session_state.insumo_vista = vista
                st.session_state.insumo_editando = None
                st.rerun()

    st.divider()

    # ===========================================================
    # VISTA: Nuevo registro
    # ===========================================================
    if st.session_state.insumo_vista == "nuevo":

        if not unidades:
            st.warning("Todavía no hay unidades de medida registradas. "
                       "Agrégalas antes de crear insumos (próximamente desde Configuración).")

        guardar, nombre, unidad_sel, costo, activo, descripcion = \
            _formulario(None, opciones_unidad, simbolo, st.session_state.insumo_form_key)

        st.caption("Se registra automáticamente quién creó este insumo y la fecha de alta.")

        if guardar:
            if not nombre.strip():
                st.error("El nombre es obligatorio.")
            elif not opciones_unidad:
                st.error("Necesitas al menos una unidad de medida antes de guardar.")
            else:
                db.insert_insumo(
                    nombre.strip(), descripcion.strip(),
                    opciones_unidad[unidad_sel], costo, activo,
                    usuario["id_usuario"]
                )
                recientes = db.get_insumos(busqueda=nombre.strip())
                codigo = recientes[0]["codigo_insumo"] if recientes else ""
                st.session_state.insumo_mensaje = f"Insumo {codigo} — '{nombre.strip()}' guardado correctamente."
                st.session_state.insumo_form_key += 1
                st.rerun()

    # ===========================================================
    # VISTA: Consultar
    # ===========================================================
    elif st.session_state.insumo_vista == "consultar":

        col_busqueda, col_estado, col_buscar = st.columns([2.5, 1.5, 0.7])
        with col_busqueda:
            busqueda = st.text_input("Buscar por nombre o código",
                                     key="busqueda_insumos",
                                     placeholder="Ej. Abono o INS-0003")
        with col_estado:
            estado_filtro = st.selectbox("Estado", ["Todos", "Activos", "Inactivos"],
                                         key="estado_filtro_insumos")
        with col_buscar:
            st.markdown("<div style='padding-top:28px;'>", unsafe_allow_html=True)
            buscar = st.button("Buscar", type="primary", use_container_width=True,
                               key="btn_buscar_insumos")
            st.markdown("</div>", unsafe_allow_html=True)

        estado_map = {"Todos": "todos", "Activos": "activos", "Inactivos": "inactivos"}

        if not buscar:
            st.info("Configura los filtros y presiona Buscar.")
        else:
            lista = db.get_insumos(busqueda=busqueda, estado=estado_map[estado_filtro])
            if not lista:
                st.info("No hay insumos que coincidan con la búsqueda.")
            else:
                st.caption(f"Mostrando {len(lista)} insumo(s)")
                df = pd.DataFrame([{
                    "ID":            i["codigo_insumo"],
                    "Nombre":        i["nombre"],
                    "Descripción":   i["descripcion"],
                    "Unidad":        i["unidad"],
                    "Costo":         f"{simbolo} {i['costo']:.2f}",
                    "Estado":        "Activo" if i["activo"] else "Inactivo",
                    "Creado por":    i["creado_por"],
                    "Fecha creación":i["fecha_creacion"],
                } for i in lista])
                st.dataframe(df, use_container_width=True, hide_index=True)

    # ===========================================================
    # VISTA: Modificar
    # ===========================================================
    elif st.session_state.insumo_vista == "modificar":

        st.subheader("Buscar insumo a modificar")
        col_buscar, col_btn = st.columns([4, 1])
        with col_buscar:
            termino = st.text_input("Código del insumo",
                                    placeholder="Ej. INS-0003")
        with col_btn:
            st.markdown("<div style='padding-top:28px;'>", unsafe_allow_html=True)
            buscar_mod = st.button("Buscar", type="primary",
                                   use_container_width=True, key="btn_buscar_ins_mod")
            st.markdown("</div>", unsafe_allow_html=True)

        if buscar_mod and termino.strip():
            resultado = db.get_insumo_by_codigo(termino.strip())
            if not resultado:
                st.session_state.insumo_editando = None
                st.warning("No se encontró ningún insumo con ese código. Verifica e intenta de nuevo (ej. INS-0003).")
            else:
                st.session_state.insumo_editando = resultado["id_insumo"]
                st.rerun()

        if st.session_state.insumo_editando:
            datos = db.get_insumo_by_id(st.session_state.insumo_editando)
            if datos:
                st.divider()
                st.caption(f"Editando: **{datos['codigo_insumo']}** — {datos['nombre']}")

                guardar, nombre, unidad_sel, costo, activo, descripcion = \
                    _formulario(datos, opciones_unidad, simbolo,
                                st.session_state.insumo_form_key)

                if guardar:
                    if not nombre.strip():
                        st.error("El nombre es obligatorio.")
                    else:
                        db.update_insumo(
                            st.session_state.insumo_editando,
                            nombre.strip(), descripcion.strip(),
                            opciones_unidad[unidad_sel], costo, activo
                        )
                        datos_act = db.get_insumo_by_id(st.session_state.insumo_editando)
                        codigo = datos_act["codigo_insumo"] if datos_act else ""
                        st.session_state.insumo_mensaje = f"Insumo {codigo} — '{nombre.strip()}' actualizado correctamente."
                        st.session_state.insumo_editando = None
                        st.session_state.insumo_form_key += 1
                        st.rerun()