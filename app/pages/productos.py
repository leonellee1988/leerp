# productos.py
# Módulo Productos — maestro con 2 vistas: Formulario y Consultar.
#
# Patrón a replicar en Clientes, Proveedores e Insumos: mismo esqueleto,
# cambian las columnas y las funciones de db.py que se llaman.
#
# Decisión de arquitectura: se eliminaron st.tabs() y se reemplazaron
# por un condicional explícito (vista_actual). Razón: st.tabs no permite
# seleccionar una pestaña programáticamente, lo que causaba comportamiento
# inconsistente al dar clic en "Editar" — a veces hacía scroll al formulario,
# a veces no, dependiendo de la posición del scroll en ese momento.
# Con el condicional, la vista cambia de forma determinista y predecible.

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
    # vista_actual: "formulario" | "consultar"
    if "producto_vista" not in st.session_state:
        st.session_state.producto_vista = "formulario"

    st.title("Productos")
    st.caption("Catálogo de productos y servicios")

    # Mensaje de éxito persistente
    if st.session_state.producto_mensaje:
        st.success(st.session_state.producto_mensaje)
        st.session_state.producto_mensaje = None

    # Catálogos cargados una sola vez — ambas vistas los usan
    categorias = db.get_categorias()
    unidades = db.get_unidades_medida()
    config = db.get_config_empresa()
    simbolo = config["moneda_simbolo"] if config else "$"
    opciones_categoria = {c["nombre"]: c["id_categoria"] for c in categorias}
    opciones_unidad = {u["nombre"]: u["id_unidad"] for u in unidades}

    # --- Navegación entre vistas (reemplaza st.tabs) ---
    editando = st.session_state.producto_editando is not None
    label_formulario = "Editar registro" if editando else "Nuevo registro"

    col_btn1, col_btn2, col_espacio = st.columns([1.5, 1.5, 6])
    with col_btn1:
        tipo_btn1 = "primary" if st.session_state.producto_vista == "formulario" else "secondary"
        if st.button(label_formulario, key="vista_formulario", type=tipo_btn1, use_container_width=True):
            st.session_state.producto_vista = "formulario"
            st.rerun()
    with col_btn2:
        tipo_btn2 = "primary" if st.session_state.producto_vista == "consultar" else "secondary"
        if st.button("Consultar", key="vista_consultar", type=tipo_btn2, use_container_width=True):
            st.session_state.producto_vista = "consultar"
            st.rerun()

    st.divider()

    # ===========================================================
    # VISTA: Formulario (Nuevo registro / Editar)
    # ===========================================================
    if st.session_state.producto_vista == "formulario":

        datos = db.get_producto_by_id(st.session_state.producto_editando) if editando else None

        if not categorias or not unidades:
            st.warning(
                "Todavía no hay categorías y/o unidades de medida registradas. "
                "Agrégalas antes de crear productos (próximamente desde Configuración)."
            )

        with st.form(f"form_producto_{st.session_state.producto_form_key}"):
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input(
                    "Nombre", value=datos["nombre"] if datos else "",
                    placeholder="Ej. Laptop, Mouse, Servicio técnico...",
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
                    value=round(float(datos["costo"]), 2) if datos else 0.0,
                    step=0.5, format="%.2f",
                )
            with col6:
                precio = st.number_input(
                    f"Precio de venta ({simbolo})", min_value=0.0,
                    value=round(float(datos["precio"]), 2) if datos else 0.0,
                    step=0.5, format="%.2f",
                )

            descripcion = st.text_area(
                "Descripción (opcional)",
                value=(datos["descripcion"] or "") if datos else "",
                placeholder="Notas adicionales del producto",
            )

            activo = st.checkbox("Producto activo", value=datos["activo"] if datos else True)

            guardar = st.form_submit_button("Guardar producto", type="primary", use_container_width=True)

        st.caption("Se registra automáticamente quién creó este producto y la fecha de alta.")

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
                    db.update_producto(
                        st.session_state.producto_editando, nombre.strip(), descripcion.strip(),
                        tipo_valor, id_categoria, id_unidad, costo, precio, activo,
                    )
                    prod_actualizado = db.get_producto_by_id(st.session_state.producto_editando)
                    codigo = prod_actualizado["codigo_producto"] if prod_actualizado else ""
                    st.session_state.producto_mensaje = f"✅ Producto {codigo} — '{nombre.strip()}' actualizado correctamente."
                    st.session_state.producto_editando = None
                else:
                    db.insert_producto(
                        nombre.strip(), descripcion.strip(), tipo_valor, id_categoria,
                        id_unidad, costo, precio, activo, usuario["id_usuario"],
                    )
                    productos_recientes = db.get_productos(busqueda=nombre.strip())
                    codigo = productos_recientes[0]["codigo_producto"] if productos_recientes else ""
                    st.session_state.producto_mensaje = f"✅ Producto {codigo} — '{nombre.strip()}' guardado correctamente."

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
            buscar = st.button("Buscar", type="primary", use_container_width=True, key="btn_buscar_productos")
            st.markdown("</div>", unsafe_allow_html=True)

        id_categoria_filtro = opciones_categoria.get(cat_filtro) if cat_filtro != "Todas" else None
        estado_map = {"Todos": "todos", "Activos": "activos", "Inactivos": "inactivos"}

        hay_filtro = busqueda.strip() or cat_filtro != "Todas" or estado_filtro != "Todos"

        if not buscar:
            st.info("Configura los filtros y presiona Buscar.")
        else:
            lista_productos = db.get_productos(
                busqueda=busqueda, id_categoria=id_categoria_filtro, estado=estado_map[estado_filtro]
            )

            if not lista_productos:
                st.info("No hay productos que coincidan con la búsqueda.")
            else:
                st.caption(f"Mostrando {len(lista_productos)} producto(s)")

                # Tabla con Costo incluido (punto 5)
                import pandas as pd

                df_tabla = pd.DataFrame([{
                    "ID": p["codigo_producto"],
                    "Nombre": p["nombre"],
                    "Categoría": p["categoria"],
                    "Descripción": p["descripcion"],
                    "Unidad": p["unidad"],
                    "Costo": f"{simbolo} {p['costo']:.2f}",
                    "Precio": f"{simbolo} {p['precio']:.2f}",
                    "Estado": "Activo" if p["activo"] else "Inactivo",
                    "Creado por": p["creado_por"]
                } for p in lista_productos])

                st.dataframe(df_tabla, use_container_width=True, hide_index=True)

                opciones_editar = {f"{p['codigo_producto']} — {p['nombre']}": p["id_producto"] for p in lista_productos}
                seleccion_editar = st.selectbox(
                    "Seleccionar producto para editar:",
                    options=[""] + list(opciones_editar.keys()),
                    key="selector_editar_producto"
                )
                if seleccion_editar:
                    st.session_state.producto_editando = opciones_editar[seleccion_editar]
                    st.session_state.producto_form_key += 1
                    st.session_state.producto_vista = "formulario"
                    st.rerun()
