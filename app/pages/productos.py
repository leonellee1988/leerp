# productos.py
# Módulo Productos — maestro con 2 partes: Nuevo registro / Editar y Consultar.
#
# Patrón a replicar en Clientes, Proveedores e Insumos: mismo esqueleto,
# cambian las columnas y las funciones de db.py que se llaman.
#
# Fixes aplicados:
# - Catálogos cargados fuera de las pestañas (ambas los usan con certeza)
# - costo separado de precio (se guarda 0.0 hasta que exista módulo Compras)
# - form_key dinámica para limpiar el formulario después de guardar o cancelar
# - Mensaje de éxito via session_state para que sobreviva al st.rerun()
#   e incluye el codigo_producto del registro recién creado/editado

import streamlit as st
import db

TIPO_LABELS = {"producto": "Producto físico", "servicio": "Servicio"}
TIPO_VALORES = {v: k for k, v in TIPO_LABELS.items()}


def mostrar():
    usuario = st.session_state.usuario_actual

    # --- Estado del módulo ---
    if "producto_editando" not in st.session_state:
        st.session_state.producto_editando = None
    if "producto_form_key" not in st.session_state:
        st.session_state.producto_form_key = 0
    if "producto_mensaje" not in st.session_state:
        st.session_state.producto_mensaje = None

    st.title("Productos")
    st.caption("Catálogo de productos y servicios")

    # Mensaje de éxito persistente (sobrevive al rerun porque vive en session_state)
    if st.session_state.producto_mensaje:
        st.success(st.session_state.producto_mensaje)
        st.session_state.producto_mensaje = None

    # Catálogos cargados aquí — fuera de cualquier pestaña — para que
    # tanto "Nuevo registro" como "Consultar" los usen con certeza,
    # sin depender del orden en que Streamlit ejecute cada tab.
    categorias = db.get_categorias()
    unidades = db.get_unidades_medida()
    config = db.get_config_empresa()
    simbolo = config["moneda_simbolo"] if config else "$"
    opciones_categoria = {c["nombre"]: c["id_categoria"] for c in categorias}
    opciones_unidad = {u["nombre"]: u["id_unidad"] for u in unidades}

    editando = st.session_state.producto_editando is not None
    tab_label = "Editar registro" if editando else "Nuevo registro"
    tab_nuevo, tab_consultar = st.tabs([tab_label, "Consultar"])

    # ----------------------------------------------------------
    # Pestaña: Nuevo registro / Editar
    # ----------------------------------------------------------
    with tab_nuevo:
        datos = db.get_producto_by_id(st.session_state.producto_editando) if editando else None

        if not categorias or not unidades:
            st.warning(
                "Todavía no hay categorías y/o unidades de medida registradas. "
                "Agrégalas antes de crear productos (próximamente desde Configuración)."
            )

        # form_key dinámica: al incrementar el número, Streamlit trata el form
        # como uno nuevo y resetea todos los campos a sus valores por defecto.
        with st.form(f"form_producto_{st.session_state.producto_form_key}"):
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input(
                    "Nombre", value=datos["nombre"] if datos else "",
                    placeholder="Ej. Laptop Intel Core i3",
                )
            with col2:
                lista_categoria = list(opciones_categoria.keys()) or ["Sin categorías"]
                nombre_cat_actual = next(
                    (n for n, i in opciones_categoria.items() if datos and i == datos["id_categoria"]), None
                )
                categoria_sel = st.selectbox(
                    "Categoría", lista_categoria,
                    index=lista_categoria.index(nombre_cat_actual) if nombre_cat_actual in lista_categoria else 0,
                )

            col3, col4, col5, col6 = st.columns(4)
            with col3:
                tipo_actual = TIPO_LABELS.get(datos["tipo"], "Producto físico") if datos else "Producto físico"
                tipo_sel = st.selectbox(
                    "Tipo", list(TIPO_LABELS.values()),
                    index=list(TIPO_LABELS.values()).index(tipo_actual),
                )
            with col4:
                lista_unidad = list(opciones_unidad.keys()) or ["Sin unidades"]
                nombre_unidad_actual = next(
                    (n for n, i in opciones_unidad.items() if datos and i == datos["id_unidad_medida"]), None
                )
                unidad_sel = st.selectbox(
                    "Unidad de medida", lista_unidad,
                    index=lista_unidad.index(nombre_unidad_actual) if nombre_unidad_actual in lista_unidad else 0,
                )
            with col5:
                costo = st.number_input(
                    f"Costo ({simbolo})", min_value=0.0,
                    value=float(datos["costo"]) if datos else 0.0,
                    step=0.5, format="%.2f",
                )
            with col6:
                precio = st.number_input(
                    f"Precio de venta ({simbolo})", min_value=0.0,
                    value=float(datos["precio"]) if datos else 0.0,
                    step=0.5, format="%.2f",
                )

            descripcion = st.text_area(
                "Descripción (opcional)",
                value=(datos["descripcion"] or "") if datos else "",
                placeholder="Notas adicionales del producto",
            )

            activo = st.checkbox("Producto activo", value=datos["activo"] if datos else True)

            col_cancelar, col_guardar = st.columns(2)
            with col_cancelar:
                cancelar = st.form_submit_button("Cancelar", use_container_width=True)
            with col_guardar:
                guardar = st.form_submit_button(
                    "Guardar producto", type="primary", use_container_width=True
                )

        st.caption("Se registra automáticamente quién creó este producto y la fecha de alta.")

        if cancelar:
            st.session_state.producto_editando = None
            st.session_state.producto_form_key += 1  # resetea el formulario
            st.rerun()

        if guardar:
            if not nombre.strip():
                st.error("El nombre es obligatorio.")
            elif not opciones_categoria or not opciones_unidad:
                st.error("Necesitas al menos una categoría y una unidad de medida antes de guardar.")
            else:
                id_categoria = opciones_categoria[categoria_sel]
                id_unidad = opciones_unidad[unidad_sel]
                tipo_valor = TIPO_VALORES[tipo_sel]

                if editando:
                    # Preserva el costo existente — el formulario no expone este campo aún.
                    # Se actualizará cuando exista el módulo de Compras.
                    db.update_producto(
                        st.session_state.producto_editando, nombre.strip(), descripcion.strip(),
                        tipo_valor, id_categoria, id_unidad, costo, precio, activo,
                        )
                    # Obtener el código del producto editado para el mensaje
                    prod_actualizado = db.get_producto_by_id(st.session_state.producto_editando)
                    codigo = prod_actualizado["codigo_producto"] if prod_actualizado else ""
                    st.session_state.producto_mensaje = f"✅ Producto {codigo} — '{nombre.strip()}' actualizado correctamente."
                    st.session_state.producto_editando = None
                else:
                    # costo = 0.0 explícito hasta que exista módulo de Compras
                    db.insert_producto(
                        nombre.strip(), descripcion.strip(), tipo_valor, id_categoria,
                        id_unidad, costo, precio, activo, usuario["id_usuario"],
                        )
                    # Obtener el código del producto recién creado para el mensaje
                    productos_recientes = db.get_productos(busqueda=nombre.strip())
                    codigo = productos_recientes[0]["codigo_producto"] if productos_recientes else ""
                    st.session_state.producto_mensaje = f"✅ Producto {codigo} — '{nombre.strip()}' guardado correctamente."

                st.session_state.producto_form_key += 1  # resetea el formulario
                st.rerun()

    # ----------------------------------------------------------
    # Pestaña: Consultar
    # ----------------------------------------------------------
    with tab_consultar:
        col_busqueda, col_categoria, col_estado = st.columns([2, 1, 1])
        with col_busqueda:
            busqueda = st.text_input("Buscar por nombre o ID", key="busqueda_productos",
                                      placeholder="Ej. Monitor o PRD-0042")
        with col_categoria:
            cat_opciones = ["Todas"] + [c["nombre"] for c in categorias]
            cat_filtro = st.selectbox("Categoría", cat_opciones, key="cat_filtro_productos")
        with col_estado:
            estado_filtro = st.selectbox("Estado", ["Todos", "Activos", "Inactivos"], key="estado_filtro_productos")

        id_categoria_filtro = opciones_categoria.get(cat_filtro) if cat_filtro != "Todas" else None
        estado_map = {"Todos": "todos", "Activos": "activos", "Inactivos": "inactivos"}

        lista_productos = db.get_productos(
            busqueda=busqueda, id_categoria=id_categoria_filtro, estado=estado_map[estado_filtro]
        )

        st.caption(f"Mostrando {len(lista_productos)} producto(s)")

        if not lista_productos:
            st.info("No hay productos que coincidan con la búsqueda.")
        else:
            encabezado = st.columns([1.2, 2.5, 1.8, 1.2, 1.2, 1.2, 1.2])
            for col, titulo in zip(encabezado, ["ID", "Nombre", "Categoría", "Unidad", "Precio", "Estado", ""]):
                col.markdown(f"<small style='color:#5B7280;'>{titulo}</small>", unsafe_allow_html=True)

            for p in lista_productos:
                c_id, c_nombre, c_cat, c_unidad, c_precio, c_estado, c_accion = st.columns(
                    [1.2, 2.5, 1.8, 1.2, 1.2, 1.2, 1.2]
                )
                c_id.write(p["codigo_producto"])
                c_nombre.write(f"**{p['nombre']}**")
                c_cat.write(p["categoria"])
                c_unidad.write(p["unidad"])
                c_precio.write(f"{simbolo} {p['precio']:.2f}")

                if p["activo"]:
                    c_estado.markdown(
                        '<span style="background:#E1F5EE;color:#085041;font-size:12px;'
                        'padding:3px 10px;border-radius:6px;">Activo</span>',
                        unsafe_allow_html=True,
                    )
                else:
                    c_estado.markdown(
                        '<span style="background:#EEF2F6;color:#5B7280;font-size:12px;'
                        'padding:3px 10px;border-radius:6px;">Inactivo</span>',
                        unsafe_allow_html=True,
                    )

                if c_accion.button("Editar", key=f"editar_producto_{p['id_producto']}", use_container_width=True):
                    st.session_state.producto_editando = p["id_producto"]
                    st.session_state.producto_form_key += 1
                    st.rerun()