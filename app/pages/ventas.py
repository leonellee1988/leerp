import streamlit as st
import pandas as pd
from datetime import date
import db


def mostrar():
    usuario = st.session_state.usuario_actual

    if st.session_state.get("modulo_anterior") != "ventas":
        st.session_state.venta_vista = "nuevo"
        st.session_state.vta_resultados = None
        _resetear_venta()
    st.session_state.modulo_anterior = "ventas"

    for k, v in [("venta_vista", "nuevo"), ("venta_mensaje", None)]:
        if k not in st.session_state:
            st.session_state[k] = v

    st.title("Ventas")
    st.caption("Registro de ventas y facturación")

    if st.session_state.venta_mensaje:
        st.success(st.session_state.venta_mensaje)
        st.session_state.venta_mensaje = None

    col_b1, col_b2, col_esp = st.columns([1.4, 1.4, 6.2])
    for col, vista, label in [
        (col_b1, "nuevo", "Nueva venta"),
        (col_b2, "consultar", "Consultar"),
    ]:
        with col:
            t = "primary" if st.session_state.venta_vista == vista else "secondary"
            if st.button(label, key=f"vista_vta_{vista}", type=t, use_container_width=True):
                st.session_state.venta_vista = vista
                if vista == "nuevo":
                    _resetear_venta()
                st.rerun()

    st.divider()

    if st.session_state.venta_vista == "nuevo":
        _vista_nueva_venta(usuario)
    elif st.session_state.venta_vista == "consultar":
        _vista_consultar()


def _resetear_venta():
    st.session_state.venta_paso = 1
    st.session_state.venta_cabecera = {
        "tipo_cliente":   "Consumidor Final",
        "id_cliente":     None,
        "nombre_cliente": "Consumidor Final",
        "fecha":          date.today(),
    }
    st.session_state.venta_lineas = []
    st.session_state.venta_linea_key = 0
    st.session_state.venta_resultados_clientes = []
    st.session_state.venta_cliente_seleccionado = None
    st.session_state.venta_prod_seleccionado = None
    st.session_state.venta_resultados_productos = []


def _vista_nueva_venta(usuario):
    for k, v in [
        ("venta_paso", 1),
        ("venta_cabecera", {"tipo_cliente": "Consumidor Final",
                            "id_cliente": None,
                            "nombre_cliente": "Consumidor Final",
                            "fecha": date.today()}),
        ("venta_lineas", []),
        ("venta_linea_key", 0),
        ("venta_resultados_clientes", []),
        ("venta_cliente_seleccionado", None),
        ("venta_prod_seleccionado", None),
        ("venta_resultados_productos", []),
    ]:
        if k not in st.session_state:
            st.session_state[k] = v

    # ===========================================================
    # PASO 1 — Cabecera
    # ===========================================================
    if st.session_state.venta_paso == 1:
        st.subheader("Paso 1 — Datos de la venta")

        tipo = st.radio(
            "Tipo de cliente",
            ["Consumidor Final", "Cliente registrado", "Buscar por NIT (FEL)"],
            horizontal=True,
            key="venta_tipo_cliente"
        )

        id_cliente = None
        nombre_cliente = "Consumidor Final"

        if tipo == "Consumidor Final":
            st.info("La venta se registrará como Consumidor Final sin NIT.")

        elif tipo == "Cliente registrado":
            clientes = db.get_clientes()
            if not clientes:
                st.warning("No hay clientes registrados. Agrega clientes primero.")
            else:
                if st.session_state.get("venta_cliente_seleccionado"):
                    cli = st.session_state.venta_cliente_seleccionado
                    st.success(f"Cliente: **{cli['codigo_cliente']} — {cli['nombre']}** | NIT: {cli['nit'] or '—'}")
                    id_cliente = cli["id_cliente"]
                    nombre_cliente = cli["nombre"]
                    if st.button("Cambiar cliente", key="btn_cambiar_cliente"):
                        st.session_state.venta_cliente_seleccionado = None
                        st.session_state.venta_resultados_clientes = []
                        st.rerun()
                else:
                    col_busq, col_btn_busq = st.columns([5, 1])
                    with col_busq:
                        busq_cli = st.text_input(
                            "Buscar por nombre o código",
                            placeholder="Ej. Ferretería López o CLI-0003",
                            key="venta_busq_cliente"
                        )
                    with col_btn_busq:
                        st.markdown("<div style='padding-top:28px;'>", unsafe_allow_html=True)
                        buscar_cli = st.button("Buscar", key="btn_buscar_cli",
                                               use_container_width=True)
                        st.markdown("</div>", unsafe_allow_html=True)

                    if buscar_cli:
                        if not busq_cli.strip():
                            st.warning("Escribe un nombre o código para buscar.")
                        else:
                            resultados = [
                                c for c in clientes
                                if busq_cli.lower() in c["nombre"].lower()
                                or busq_cli.lower() in c["codigo_cliente"].lower()
                            ]
                            if not resultados:
                                st.session_state.venta_resultados_clientes = []
                                st.warning("No se encontró ningún cliente.")
                            else:
                                st.session_state.venta_resultados_clientes = resultados

                    for c in st.session_state.get("venta_resultados_clientes", [])[:10]:
                        col_info, col_sel = st.columns([5, 1])
                        col_info.write(f"**{c['codigo_cliente']}** — {c['nombre']} | NIT: {c['nit'] or '—'}")
                        if col_sel.button("Seleccionar", key=f"sel_cli_{c['id_cliente']}"):
                            st.session_state.venta_cliente_seleccionado = c
                            st.session_state.venta_resultados_clientes = []
                            st.rerun()

        elif tipo == "Buscar por NIT (FEL)":
            st.info("Módulo FEL disponible próximamente. Selecciona otra opción por ahora.")

        if tipo != "Buscar por NIT (FEL)":
            fecha = st.date_input("Fecha de la venta", value=date.today(),
                                  key="venta_fecha")
            st.write("")
            _, col_btn, _ = st.columns([3, 2, 3])
            with col_btn:
                continuar = st.button("Continuar", type="primary",
                                      use_container_width=True, key="btn_continuar_venta")
        else:
            fecha = date.today()
            continuar = False

        if continuar:
            if tipo == "Cliente registrado" and not id_cliente:
                st.error("Selecciona un cliente antes de continuar.")
            elif tipo == "Buscar por NIT (FEL)":
                st.error("Selecciona otra opción de cliente por ahora.")
            else:
                st.session_state.venta_cabecera = {
                    "tipo_cliente":   tipo,
                    "id_cliente":     id_cliente,
                    "nombre_cliente": nombre_cliente,
                    "fecha":          fecha,
                }
                st.session_state.venta_paso = 2
                st.rerun()

    # ===========================================================
    # PASO 2 — Líneas de detalle
    # ===========================================================
    elif st.session_state.venta_paso == 2:
        cab = st.session_state.venta_cabecera
        config = db.get_config_empresa()
        simbolo = config["moneda_simbolo"] if config else "Q"
        linea_key = st.session_state.venta_linea_key

        st.subheader("Paso 2 — Líneas de venta")

        col_i1, col_i2, col_i3 = st.columns(3)
        col_i1.caption("Cliente")
        col_i1.write(f"**{cab['nombre_cliente']}**")
        col_i2.caption("Fecha")
        col_i2.write(f"**{cab['fecha']}**")
        col_i3.caption("Líneas")
        col_i3.write(f"**{len(st.session_state.venta_lineas)}**")

        st.divider()

        # --- Agregar línea ---
        productos = db.get_productos_activos()
        if not productos:
            st.warning("No hay productos activos registrados.")
        else:
            if st.session_state.get("venta_prod_seleccionado"):
                prod = st.session_state.venta_prod_seleccionado
                st.success(
                    f"Producto: **{prod['codigo_producto']} — {prod['nombre']}** | "
                    f"Precio sugerido: {simbolo} {prod['precio']:.2f}"
                )
                if st.button("Cambiar producto", key="btn_cambiar_prod"):
                    st.session_state.venta_prod_seleccionado = None
                    st.session_state.venta_resultados_productos = []
                    st.rerun()

                col_q, col_pr, col_btn = st.columns([1.5, 1.5, 1])
                with col_q:
                    cantidad = st.number_input(
                        "Cantidad", min_value=0.01, value=1.0,
                        step=1.0, format="%.2f",
                        key=f"venta_cantidad_{linea_key}"
                    )
                with col_pr:
                    precio_linea = st.number_input(
                        f"Precio ({simbolo})",
                        min_value=0.0,
                        value=round(float(prod["precio"]), 2),
                        step=0.50, format="%.2f",
                        key=f"venta_precio_{linea_key}"
                    )
                with col_btn:
                    st.markdown("<div style='padding-top:28px;'>", unsafe_allow_html=True)
                    agregar = st.button("Agregar", type="primary",
                                        use_container_width=True,
                                        key=f"btn_agregar_linea_{linea_key}")
                    st.markdown("</div>", unsafe_allow_html=True)
            else:
                agregar = False
                cantidad = 1.0
                precio_linea = 0.0

                col_busq_p, col_btn_busq_p = st.columns([5, 1])
                with col_busq_p:
                    busq_prod = st.text_input(
                        "Buscar producto por nombre o código",
                        placeholder="Ej. Monitor o PRD-0006",
                        key=f"venta_busq_prod_{linea_key}"
                    )
                with col_btn_busq_p:
                    st.markdown("<div style='padding-top:28px;'>", unsafe_allow_html=True)
                    buscar_prod = st.button("Buscar", key="btn_buscar_prod",
                                            use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)

                if buscar_prod:
                    if not busq_prod.strip():
                        st.warning("Escribe un nombre o código para buscar.")
                    else:
                        prods_filtrados = [
                            p for p in productos
                            if busq_prod.lower() in p["nombre"].lower()
                            or busq_prod.lower() in p["codigo_producto"].lower()
                        ]
                        if not prods_filtrados:
                            st.session_state.venta_resultados_productos = []
                            st.warning("No se encontró ningún producto.")
                        else:
                            st.session_state.venta_resultados_productos = prods_filtrados

                for p in st.session_state.get("venta_resultados_productos", [])[:10]:
                    col_info, col_sel = st.columns([5, 1])
                    col_info.write(
                        f"**{p['codigo_producto']}** — {p['nombre']} | "
                        f"{simbolo} {p['precio']:.2f}"
                    )
                    if col_sel.button("Seleccionar", key=f"sel_prod_{p['id_producto']}"):
                        st.session_state.venta_prod_seleccionado = p
                        st.session_state.venta_resultados_productos = []
                        st.rerun()

            if agregar:
                if not st.session_state.get("venta_prod_seleccionado"):
                    st.error("Selecciona un producto.")
                elif cantidad <= 0:
                    st.error("La cantidad debe ser mayor a cero.")
                else:
                    prod = st.session_state.venta_prod_seleccionado
                    # R2 — Validar productos duplicados en la misma venta
                    ya_existe = any(
                        l["id_producto"] == prod["id_producto"]
                        for l in st.session_state.venta_lineas
                    )
                    if ya_existe:
                        st.error(
                            f"'{prod['nombre']}' ya está en esta venta. "
                            "Edita la cantidad en la línea existente."
                        )
                    else:
                        linea = {
                            "id_producto": prod["id_producto"],
                            "codigo":      prod["codigo_producto"],
                            "nombre":      prod["nombre"],
                            "cantidad":    cantidad,
                            "precio":      precio_linea,
                            "subtotal":    round(cantidad * precio_linea, 2),
                        }
                        st.session_state.venta_lineas.append(linea)
                        st.session_state.venta_prod_seleccionado = None
                        st.session_state.venta_resultados_productos = []
                        st.session_state.venta_linea_key += 1
                        st.rerun()

        st.divider()

        # --- Tabla de líneas acumuladas ---
        lineas = st.session_state.venta_lineas
        if not lineas:
            st.info("Agrega al menos un producto para continuar.")
        else:
            enc = st.columns([1.2, 2.5, 1, 1.5, 1.5, 0.8])
            for col, titulo in zip(enc, ["Código", "Producto",
                                         "Cantidad", "Precio", "Subtotal", ""]):
                col.markdown(
                    f"<small style='color:#5B7280;font-weight:600;'>{titulo}</small>",
                    unsafe_allow_html=True
                )

            for idx, linea in enumerate(lineas):
                c1, c2, c3, c4, c5, c6 = st.columns([1.2, 2.5, 1, 1.5, 1.5, 0.8])
                c1.write(linea["codigo"])
                c2.write(f"**{linea['nombre']}**")
                c3.write(f"{linea['cantidad']:.2f}")
                c4.write(f"{simbolo} {linea['precio']:.2f}")
                c5.write(f"{simbolo} {linea['subtotal']:.2f}")
                if c6.button("X", key=f"del_linea_{idx}", help="Eliminar esta línea"):
                    st.session_state.venta_lineas.pop(idx)
                    st.rerun()

            total = sum(l["subtotal"] for l in lineas)
            st.markdown(
                f"<div style='text-align:right; font-size:18px; font-weight:700;"
                f"color:#0A2540; padding:12px 0;'>"
                f"Total: {simbolo} {total:,.2f}</div>",
                unsafe_allow_html=True
            )

            st.divider()
            col_c, col_g = st.columns(2)
            with col_c:
                if st.button("Cancelar venta", use_container_width=True,
                             key="btn_cancelar_venta"):
                    _resetear_venta()
                    st.rerun()
            with col_g:
                if st.button("Guardar venta", type="primary",
                             use_container_width=True, key="btn_guardar_venta"):
                    id_venta = db.insert_venta(
                        cab["fecha"], cab["id_cliente"],
                        usuario["id_usuario"], lineas
                    )
                    codigo_venta = db.get_venta_codigo(id_venta)
                    st.session_state.venta_mensaje = (
                        f"Venta {codigo_venta} registrada correctamente — "
                        f"{simbolo} {total:,.2f}"
                    )
                    _resetear_venta()
                    st.rerun()


def _vista_consultar():
    """Consultar ventas — tabla plana única, grano de línea de producto
    (una fila por producto vendido, mismo shape que el CSV de descarga).

    Los resultados se guardan en session_state (vta_resultados) porque
    cualquier otro widget de la página (ej. el botón de descarga) dispara
    un rerun de Streamlit — sin esto, el botón 'Buscar' es la única fuente
    de los datos y cualquier otra interacción los "borra" de pantalla.
    """
    config = db.get_config_empresa()
    simbolo = config["moneda_simbolo"] if config else "Q"

    col_f1, col_f2, col_f3, col_btn = st.columns([1.5, 1.5, 1.5, 0.7])
    with col_f1:
        fecha_desde = st.date_input("Desde", value=date.today().replace(day=1),
                                    key="vta_fecha_desde")
    with col_f2:
        fecha_hasta = st.date_input("Hasta", value=date.today(),
                                    key="vta_fecha_hasta")
    with col_f3:
        busqueda = st.text_input("Código o cliente",
                                 placeholder="Ej. VTA-0001",
                                 key="vta_busqueda")
    with col_btn:
        st.markdown("<div style='padding-top:28px;'>", unsafe_allow_html=True)
        buscar = st.button("Buscar", type="primary",
                           use_container_width=True, key="btn_buscar_ventas")
        st.markdown("</div>", unsafe_allow_html=True)

    if buscar:
        st.session_state.vta_resultados = db.get_ventas(fecha_desde, fecha_hasta, busqueda)

    lineas = st.session_state.get("vta_resultados")

    if lineas is None:
        st.info("Configura los filtros y presiona Buscar.")
        return
    if not lineas:
        st.info("No hay ventas que coincidan con la búsqueda.")
        return

    # Total por venta único (una venta puede tener varias líneas, y todas
    # traen el mismo total_venta repetido — se toma una sola vez por id_venta).
    totales_por_venta = {l["id_venta"]: l["total_venta"] for l in lineas}

    st.caption(f"Mostrando {len(totales_por_venta)} venta(s) — {len(lineas)} línea(s) de producto")

    df_tabla = pd.DataFrame([{
        "Venta":     l["codigo_venta"],
        "Fecha":     l["fecha_venta"],
        "Cliente":   l["nombre_cliente"],
        "Producto":  l["nombre_producto"],
        "Categoría": l["categoria"],
        "Cantidad":  f"{l['cantidad']:.2f}",
        "Precio":    f"{simbolo} {l['precio_unitario']:.2f}",
        "Subtotal":  f"{simbolo} {l['subtotal']:.2f}",
        "Costo":     f"{simbolo} {l['costo']:.2f}",
        "Margen":    f"{simbolo} {l['margen']:.2f}",
        "Estado":    "Anulada" if l["anulada"] else "Activa",
    } for l in lineas])

    st.dataframe(df_tabla, use_container_width=True, hide_index=True)

    total_periodo = sum(totales_por_venta.values())
    st.markdown(
        f"<div style='text-align:right; font-size:16px; font-weight:700;"
        f"color:#0A2540; padding:8px 0;'>"
        f"Total período: {simbolo} {total_periodo:,.2f}</div>",
        unsafe_allow_html=True
    )

    st.divider()

    # --- CSV: mismo grano de línea que la tabla en pantalla ---
    df_csv = pd.DataFrame([{
        "Codigo venta":    l["codigo_venta"],
        "Fecha":           l["fecha_venta"],
        "Cliente":         l["nombre_cliente"],
        "NIT cliente":     l["nit_cliente"],
        "Codigo producto": l["codigo_producto"],
        "Producto":        l["nombre_producto"],
        "Categoria":       l["categoria"],
        "Cantidad":        l["cantidad"],
        "Precio unitario": l["precio_unitario"],
        "Subtotal linea":  l["subtotal"],
        "Costo unitario":  l["costo"],
        "Margen linea":    l["margen"],
        "Total venta":     l["total_venta"],
        "Estado":          "Anulada" if l["anulada"] else "Activa",
        "Registrado por":  l["registrado_por"],
    } for l in lineas])

    st.download_button(
        "Descargar CSV (detalle completo)",
        data=df_csv.to_csv(index=False).encode("utf-8"),
        file_name=f"ventas_{fecha_desde}_{fecha_hasta}.csv",
        mime="text/csv",
    )