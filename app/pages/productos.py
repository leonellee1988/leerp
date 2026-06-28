import streamlit as st
import pandas as pd
import db

TIPO_LABELS = {"producto": "Producto físico", "servicio": "Servicio"}
TIPO_VALORES = {v: k for k, v in TIPO_LABELS.items()}


def _formulario(datos, opciones_categoria, opciones_unidad, simbolo, form_key):
    with st.form(f"form_producto_{form_key}"):
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre", value=datos["nombre"] if datos else "",
                                   placeholder="Ej. Laptop, Mouse, Servicio técnico...")
        with col2:
            lista_cat = list(opciones_categoria.keys()) or ["Sin categorías"]
            cat_actual = next((n for n, i in opciones_categoria.items()
                               if datos and i == datos["id_categoria"]), None)
            categoria_sel = st.selectbox("Categoría", lista_cat,
                                         index=lista_cat.index(cat_actual) if cat_actual in lista_cat else 0)

        col3, col4, col5, col6 = st.columns(4)
        with col3:
            tipo_actual = TIPO_LABELS.get(datos["tipo"], "Producto físico") if datos else "Producto físico"
            tipo_sel = st.selectbox("Tipo", list(TIPO_LABELS.values()),
                                    index=list(TIPO_LABELS.values()).index(tipo_actual))
        with col4:
            lista_u = list(opciones_unidad.keys()) or ["Sin unidades"]
            u_actual = next((n for n, i in opciones_unidad.items()
                             if datos and i == datos["id_unidad_medida"]), None)
            unidad_sel = st.selectbox("Unidad de medida", lista_u,
                                      index=lista_u.index(u_actual) if u_actual in lista_u else 0)
        with col5:
            costo = st.number_input(f"Costo ({simbolo})", min_value=0.0,
                                    value=round(float(datos["costo"]), 2) if datos else 0.0,
                                    step=0.5, format="%.2f")
        with col6:
            precio = st.number_input(f"Precio de venta ({simbolo})", min_value=0.0,
                                     value=round(float(datos["precio"]), 2) if datos else 0.0,
                                     step=0.5, format="%.2f")

        descripcion = st.text_area("Descripción (opcional)",
                                   value=(datos["descripcion"] or "") if datos else "",
                                   placeholder="Notas adicionales del producto")
        activo = st.checkbox("Producto activo", value=datos["activo"] if datos else True)

        _, col_g, _ = st.columns([2, 3, 2])
        with col_g:
            guardar = st.form_submit_button("Guardar producto", type="primary", use_container_width=True)

    return guardar, nombre, categoria_sel, tipo_sel, unidad_sel, costo, precio, descripcion, activo


def mostrar():
    usuario = st.session_state.usuario_actual

    if st.session_state.get("modulo_anterior") != "productos":
        st.session_state.producto_vista = "nuevo"
        st.session_state.producto_editando = None
    st.session_state.modulo_anterior = "productos"

    for k, v in [("producto_editando", None), ("producto_form_key", 0),
                 ("producto_mensaje", None), ("producto_vista", "nuevo")]:
        if k not in st.session_state:
            st.session_state[k] = v

    st.title("Productos")
    st.caption("Catálogo de productos y servicios")

    if st.session_state.producto_mensaje:
        st.success(st.session_state.producto_mensaje)
        st.session_state.producto_mensaje = None

    categorias = db.get_categorias()
    unidades = db.get_unidades_medida()
    config = db.get_config_empresa()
    simbolo = config["moneda_simbolo"] if config else "$"
    opciones_categoria = {c["nombre"]: c["id_categoria"] for c in categorias}
    opciones_unidad = {u["nombre"]: u["id_unidad"] for u in unidades}

    col_b1, col_b2, col_b3, col_esp = st.columns([1.4, 1.4, 1.4, 4.8])
    for col, vista, label in [
        (col_b1, "nuevo", "Nuevo registro"),
        (col_b2, "consultar", "Consultar"),
        (col_b3, "modificar", "Modificar"),
    ]:
        with col:
            t = "primary" if st.session_state.producto_vista == vista else "secondary"
            if st.button(label, key=f"vista_{vista}", type=t, use_container_width=True):
                st.session_state.producto_vista = vista
                st.session_state.producto_editando = None
                st.rerun()

    st.divider()

    # ===========================================================
    # VISTA: Nuevo registro
    # ===========================================================
    if st.session_state.producto_vista == "nuevo":

        if not categorias or not unidades:
            st.warning("Todavía no hay categorías y/o unidades de medida registradas. "
                       "Agrégalas antes de crear productos (próximamente desde Configuración).")

        guardar, nombre, categoria_sel, tipo_sel, unidad_sel, costo, precio, descripcion, activo = \
            _formulario(None, opciones_categoria, opciones_unidad, simbolo,
                        st.session_state.producto_form_key)

        st.caption("Se registra automáticamente quién creó este producto y la fecha de alta.")

        if guardar:
            if not nombre.strip():
                st.error("El nombre es obligatorio.")
            elif not opciones_categoria or not opciones_unidad:
                st.error("Necesitas al menos una categoría y una unidad de medida antes de guardar.")
            else:
                db.insert_producto(
                    nombre.strip(), descripcion.strip(), TIPO_VALORES[tipo_sel],
                    opciones_categoria[categoria_sel], opciones_unidad[unidad_sel],
                    costo, precio, activo, usuario["id_usuario"],
                )
                recientes = db.get_productos(busqueda=nombre.strip())
                codigo = recientes[0]["codigo_producto"] if recientes else ""
                st.session_state.producto_mensaje = f"Producto {codigo} — '{nombre.strip()}' guardado correctamente."
                st.session_state.producto_form_key += 1
                st.rerun()

    # ===========================================================
    # VISTA: Consultar
    # ===========================================================
    elif st.session_state.producto_vista == "consultar":

        col_busqueda, col_categoria, col_estado, col_buscar = st.columns([1.5, 1.2, 1.2, 0.7])
        with col_busqueda:
            busqueda = st.text_input("Buscar por nombre o ID", key="busqueda_productos",
                                     placeholder="Ej. Monitor o PRD-0042")
        with col_categoria:
            cat_opciones = ["Todas"] + [c["nombre"] for c in categorias]
            cat_filtro = st.selectbox("Categoría", cat_opciones, key="cat_filtro_productos")
        with col_estado:
            estado_filtro = st.selectbox("Estado", ["Todos", "Activos", "Inactivos"],
                                         key="estado_filtro_productos")
        with col_buscar:
            st.markdown("<div style='padding-top:28px;'>", unsafe_allow_html=True)
            buscar = st.button("Buscar", type="primary", use_container_width=True,
                               key="btn_buscar_productos")
            st.markdown("</div>", unsafe_allow_html=True)

        id_categoria_filtro = opciones_categoria.get(cat_filtro) if cat_filtro != "Todas" else None
        estado_map = {"Todos": "todos", "Activos": "activos", "Inactivos": "inactivos"}

        if not buscar:
            st.info("Configura los filtros y presiona Buscar.")
        else:
            lista_productos = db.get_productos(
                busqueda=busqueda, id_categoria=id_categoria_filtro,
                estado=estado_map[estado_filtro]
            )
            if not lista_productos:
                st.info("No hay productos que coincidan con la búsqueda.")
            else:
                st.caption(f"Mostrando {len(lista_productos)} producto(s)")
                df_tabla = pd.DataFrame([{
                    "ID":            p["codigo_producto"],
                    "Nombre":        p["nombre"],
                    "Categoría":     p["categoria"],
                    "Descripción":   p["descripcion"],
                    "Unidad":        p["unidad"],
                    "Costo":         f"{simbolo} {p['costo']:.2f}",
                    "Precio":        f"{simbolo} {p['precio']:.2f}",
                    "Estado":        "Activo" if p["activo"] else "Inactivo",
                    "Creado por":    p["creado_por"],
                    "Fecha creación":p["fecha_creacion"],
                } for p in lista_productos])
                st.dataframe(df_tabla, use_container_width=True, hide_index=True)

    # ===========================================================
    # VISTA: Modificar
    # ===========================================================
    elif st.session_state.producto_vista == "modificar":

        st.subheader("Buscar producto a modificar")
        col_buscar, col_btn = st.columns([4, 1])
        with col_buscar:
            termino = st.text_input("Ingrese el código del producto",
                                    placeholder="Ej. PRD-0007")
        with col_btn:
            st.markdown("<div style='padding-top:28px;'>", unsafe_allow_html=True)
            buscar_mod = st.button("Buscar", type="primary",
                                   use_container_width=True, key="btn_buscar_mod")
            st.markdown("</div>", unsafe_allow_html=True)

        if buscar_mod and termino.strip():
            resultados = db.get_productos(busqueda=termino.strip())
            if not resultados:
                st.session_state.producto_editando = None
                st.warning("No se encontró ningún producto con ese código.")
            elif len(resultados) == 1:
                st.session_state.producto_editando = resultados[0]["id_producto"]
                st.rerun()
            else:
                st.warning("El código ingresado devolvió más de un resultado. Ingresa el código exacto (ej. PRD-0007).")

        if st.session_state.producto_editando:
            datos = db.get_producto_by_id(st.session_state.producto_editando)
            if datos:
                st.divider()
                st.caption(f"Editando: **{datos['codigo_producto']}** — {datos['nombre']}")

                guardar, nombre, categoria_sel, tipo_sel, unidad_sel, costo, precio, descripcion, activo = \
                    _formulario(datos, opciones_categoria, opciones_unidad, simbolo,
                                st.session_state.producto_form_key)

                if guardar:
                    if not nombre.strip():
                        st.error("El nombre es obligatorio.")
                    else:
                        db.update_producto(
                            st.session_state.producto_editando, nombre.strip(),
                            descripcion.strip(), TIPO_VALORES[tipo_sel],
                            opciones_categoria[categoria_sel], opciones_unidad[unidad_sel],
                            costo, precio, activo,
                        )
                        prod = db.get_producto_by_id(st.session_state.producto_editando)
                        codigo = prod["codigo_producto"] if prod else ""
                        st.session_state.producto_mensaje = f"Producto {codigo} — '{nombre.strip()}' actualizado correctamente."
                        st.session_state.producto_editando = None
                        st.session_state.producto_form_key += 1
                        st.rerun()