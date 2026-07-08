# Bitácora del Proyecto — LEERP

## 2026

### Sesión 1 — Kickoff y definición de alcance
- Equipo conformado: Mike (ERP/desarrollo), Hank (BD/BI), Walter (imagen corporativa),
  Edwin (project manager)
- Objetivo definido: generalizar el ERP piloto GuateCompost en un producto
  comercializable para micro y pequeñas empresas — no específico a un solo
  cliente o industria
- Stack confirmado: Python, Streamlit, PostgreSQL, Neon Cloud
- Material de marca recibido: logo (versión clara/oscura), ícono, paleta de
  colores (Navy #0A2540, Teal #00C2A8, Blue #3A7CA5, Sky #7EB8D4,
  Ice #F4F8FC, White #FFFFFF)
- Preguntas estratégicas planteadas al PM: modelo de despliegue (multi-tenant
  vs. aislado), modelo de negocio, viabilidad de un módulo de producción

### Sesión 2 — Revisión de GuateCompost y decisiones estratégicas
- README, bitácora y ERD de GuateCompost compartidos como contexto histórico
- Hallazgo: el campo `activo` ya existía en la BD real de GuateCompost
  (agregado en su Sesión 7 vía `ALTER TABLE`) pero nunca se reflejó en el ERD
  documentado — lección aplicada: en LEERP, `activo` y auditoría son
  estándar de plantilla desde el diseño base, no parches posteriores
- Decisión: módulo de producción/manufactura diferido 3-5 años
- Decisión: modelo de despliegue = una base de datos Neon aislada por cliente
  (no multi-tenant compartido)
- Decisión: modelo de negocio = mismo código base, configuración superficial
  por cliente (nombre, moneda, logo)
- Decisión: catálogos controlados (`unidad_medida`, `categoria`) en vez de
  texto libre, para consistencia de BI entre clientes
- Decisión: distinguir producto físico vs. servicio en el catálogo
- Decisión: identidad de marca co-branded (referencia: experiencia de Edwin
  con SAP) — LEERP visible + nombre del cliente

### Sesión 3 — Primer esquema de base de datos
- `leerp_schema.sql` generado: `config_empresa`, `usuarios`, catálogos
  (`unidad_medida`, `categoria`), maestros (`producto`, `cliente`,
  `proveedor`, `insumo`) con `activo` y auditoría estándar, tablas
  transaccionales (`venta`, `compra`, `gasto`) con trazabilidad por
  `id_usuario`
- Decisión: montos en `NUMERIC(15,2)` — nunca `float`, para evitar errores
  de precisión en dinero
- `auth_utils.py` creado: `hash_password()` / `verificar_password()` con
  `bcrypt` — contraseñas nunca se guardan en texto plano

### Sesión 4 — Corrección de proceso: mapa de carpetas y roles
- Corrección del equipo: definir la estructura de carpetas del proyecto
  antes de seguir generando código
- Estructura definida: `app/` (`main.py`, `auth.py`, `db.py`, `config.py`,
  `pages/`, `utils/`), `scripts/`, `sql/`, `docs/`
- 4 roles definidos: `admin` (total), `captura` (solo ingreso),
  `analista` (ingreso + consultas/reportes), `visor` (solo consulta)
- `permisos.py` creado: matriz de permisos por rol y módulo
- `leerp_schema.sql` actualizado: `CHECK` de `usuarios.rol` con los 4 roles

### Sesión 5 — Bootstrap y documentación base
- Decisión: los usuarios se crean desde el ERP, no manualmente en Neon — el
  hash de contraseña debe generarse en código, no en SQL
- Excepción resuelta: `scripts/seed_admin.py` — bootstrap del primer usuario
  admin de cada cliente nuevo (problema huevo-y-gallina: se necesita un
  admin para crear usuarios, pero no existe ninguno al desplegar)
- `.env.example`, `.gitignore`, `requirements.txt` generados
- `README.md` generado — documento central del proyecto

### Sesión 6 — Primeras pruebas en ambiente real (Fedora Linux)
- Entorno virtual creado, dependencias instaladas desde `requirements.txt`
- Conexión DBeaver ↔ Neon establecida
- Bug resuelto: `.gitignore` sin el punto inicial — git no lo reconocía
- Bug resuelto: error `relation "config_empresa" does not exist` — causa:
  se ejecutó una sola instrucción (`Ctrl+Enter`) en vez del script completo
- **EUREKA 1:** esquema completo corrido en Neon con `Alt+X`
  (Execute SQL Script) — 15 tablas creadas
- **EUREKA 2:** primer usuario admin creado con `seed_admin.py` y
  verificado en DBeaver (`password_hash` confirmado como hash, no texto
  plano)

### Sesión 7 — Pantalla de login (`auth.py`)
- Hallazgo: `main.py` y `db.py` nunca se habían generado para LEERP (solo
  existían para GuateCompost) — corregido, versiones base creadas
- `auth.py` creado: login con identidad LEERP, paleta de marca, patrón
  co-branded ("Ingresando a [cliente]")
- Hallazgo de seguridad: el menú automático de páginas de Streamlit no
  respeta el gate de login — cualquier página en `app/pages/` es accesible
  directo sin pasar por `main.py`. Decisión: ocultarlo y construir
  navegación centralizada manual (mismo patrón que GuateCompost)
- Bug resuelto: cuadro blanco vacío en el login — un `<div>` HTML
  abierto/cerrado en llamadas separadas de `st.markdown()` no anida como se
  esperaba en Streamlit. Solución: `st.container(key=...)`
- Concepto aprendido: Streamlit aplica varios estilos (gap, padding) como
  estilo inline vía JS, que gana sobre CSS externo sin `!important`
- Varias rondas de ajuste de espaciado y selectores CSS, resueltas con
  ayuda de las herramientas de desarrollador del navegador (Inspeccionar
  elemento) para confirmar la estructura real del DOM en vez de adivinar

### Sesión 8 — Pulido final del login (con apoyo de consultoría externa)
- Hot reload configurado: `.streamlit/config.toml` con `runOnSave = true`
- Causa raíz real de la baja legibilidad de las etiquetas
  "Usuario"/"Contraseña" identificada: contraste de color (texto claro del
  tema oscuro de Streamlit sobre tarjeta blanca), no un problema de
  espaciado como se había asumido
- Espaciado final del formulario ajustado
- `.block-container` ajustado para centrar verticalmente la tarjeta
- Favicon implementado: `app/assets/leerp-icon.ico`, referenciado en
  `st.set_page_config()`

### Sesión 9 — Diseño de la pantalla de inicio (home) y sidebar
- Revisión del "home" actual de GuateCompost como referencia —
  observaciones: color activo del sidebar fuera de paleta (rojo), tarjetas
  de módulo todas con el mismo color genérico, iconos en emoji
- Propuesta de diseño aprobada por el PM: sidebar agrupado por sección
  (General / Maestros / Transacciones / Inventario, alineado a
  `permisos.py`), color activo en teal de marca, iconos en vez de emoji,
  panel principal en fondo claro para mejor lectura en uso prolongado
- Pendiente para la siguiente sesión: construcción real en Streamlit del
  sidebar + home, conexión de `permisos.py` para filtrar módulos visibles
  por rol, módulos reales (`productos.py`, `clientes.py`, etc.)
  generalizados desde el patrón de GuateCompost

  # Cosas a revisar:

  1. Se perdió el "ojito" en el input de la contraseña ✅ Resuelto en Sesión 12
  2. Revisar color="currentColor" de iconos.py — pendiente

### Sesión 10 — Construcción real del sidebar, home e íconos SVG

- `main.py` construido con navegación real: sidebar agrupado por sección,
  filtrado por `permisos.py` según rol, botón activo en teal de marca
- Patrón de navegación implementado: `st.session_state.pagina_actual` como
  fuente de verdad — botones del sidebar y tarjetas del home actualizan
  este valor y disparan `st.rerun()`
- `utils/navegacion.py` creado: `NAV_STRUCTURE` centralizado —
  agregar un módulo al menú = una entrada en este archivo, sin tocar
  `main.py`
- `utils/iconos.py` creado: diccionario `ICONOS` con SVG estilo Lucide
  (outline, stroke-based) para los 12 módulos del sistema. Función
  `get_icono(key)` devuelve el SVG listo para `st.markdown`
- Bug resuelto (varias rondas): botones del sidebar se veían centrados a
  pesar de `justify-content: flex-start` en el CSS. Causa raíz: Streamlit
  anida el texto del botón en un `<div>` interno con clase autogenerada
  (`e12tamyi2` en la versión actual) que trae su propio centrado. Solución
  final: selector `button div[class*="e12tamyi2"]`
- Técnica establecida: ante cualquier CSS que "no aplica", confirmar con
  el inspector del navegador (Calculada) el selector y valor real antes de
  seguir iterando — esta lección se repitió en Sesiones 11 y 12
- Pantalla home: tarjetas de módulo con ícono, nombre y botón "Abrir" —
  doble vía de navegación (sidebar + home), decisión consciente que
  sigue el patrón estándar de ERPs (SAP, Odoo, Dynamics)
- `COLOR_GRUPO` agregado a `navegacion.py`: colores de fondo e ícono
  por grupo (Maestros, Transacciones, etc.) para las tarjetas del home
- Seguridad reforzada en enrutamiento: validación de `permisos.tiene_permiso`
  no solo al construir el sidebar sino también al momento de renderizar —
  previene acceso a módulos si `pagina_actual` quedó en sesión previa

### Sesión 11 — Módulo Productos (primer maestro)

- `pages/productos.py` construido: patrón de 2 pestañas definido para
  todos los maestros: "Nuevo registro / Editar" y "Consultar"
- Decisión de UX (confirmada por Ross con experiencia ERP): botón "Abrir"
  en tarjetas del home no es redundante con el sidebar — doble vía de
  navegación estándar en el mercado
- Campos del formulario: Nombre, Categoría, Tipo (físico/servicio),
  Unidad de medida, Precio de venta, Descripción, activo
- Tabla de Consultar: filtros por nombre/código, categoría y estado
  (Activo/Inactivo); columnas: ID, Nombre, Categoría, Unidad, Precio,
  Estado, botón Editar
- Flujo "Editar": clic en botón Editar de la tabla → `producto_editando`
  en session_state → pestaña cambia a "Editar registro" precargada con
  datos existentes
- `db.py` ampliado: `get_categorias()`, `get_unidades_medida()`,
  `get_productos()`, `get_producto_by_id()`, `insert_producto()`,
  `update_producto()`
- Bug identificado y corregido: catálogos (`categorias`, `unidades`)
  originalmente cargados dentro de `tab_nuevo` — fragilidad: tab_consultar
  los usaba pero no garantizaba que ya estuvieran cargados. Solución:
  mover las cargas al inicio de `mostrar()`, fuera de cualquier pestaña
- Bug corregido: `insert_producto` y `update_producto` recibían `precio`
  dos veces (una para `costo` y otra para `precio`). `costo` y `precio`
  son campos distintos en el esquema. Solución: `costo=0.0` explícito
  por ahora, con comentario indicando que se actualizará cuando exista
  el módulo de Compras con precio de costo real por proveedor
- Validación funcional: mensaje de advertencia amarillo si no hay
  categorías ni unidades registradas — obliga a cargar catálogos antes
  de crear el primer producto
- Patrón establecido para replicar en Clientes, Proveedores e Insumos:
  mismo esqueleto, cambian columnas y funciones de `db.py`

### Sesión 12 — Esquema v1.1: códigos, auditoría y Kardex

- `leerp_schema.sql` reconstruido a v1.1 — cambios principales:
- **Códigos legibles** (`codigo_producto`, `codigo_cliente`, etc.):
  columna `GENERATED ALWAYS AS ... STORED` en PostgreSQL — se genera
  automáticamente al insertar, nunca se manda en un `INSERT`, nunca
  se usa como foreign key (el `id_` numérico sigue siendo la relación
  real entre tablas). El código es la cara que ve el usuario; el `id_`
  es el esqueleto que sostiene la BD
- Tablas con código: `producto` (PRD-), `cliente` (CLI-), `proveedor`
  (PRV-), `insumo` (INS-), `venta_cabecera` (VTA-), `compra_cabecera`
  (CMP-), `gasto_cabecera` (GAS-), `movimiento_inventario` (MOV-)
- Tablas SIN código propio: `usuarios` (se identifica por login),
  catálogos (`categoria`, `unidad_medida`, `config_empresa`),
  todos los `*_detalle` (no tienen identidad para el usuario fuera de
  su cabecera)
- **`id_usuario_creacion`** agregado a los 4 maestros — antes solo
  existía en las transaccionales como `id_usuario`. Mismo propósito:
  trazabilidad de quién creó cada registro
- **Kardex** (`movimiento_inventario`) reemplaza `inventario_inicial`:
  el modelo `inicial + compras - ventas` heredado de GuateCompost no
  permite saber cuándo ni por qué se produjo una discrepancia.
  El Kardex registra cada movimiento individualmente — tipos:
  `inventario_inicial`, `entrada_compra`, `salida_venta`,
  `ajuste_positivo`, `ajuste_negativo`
- Decisión: el costo real de un producto se conocerá a través de
  las compras (módulo futuro), no en el formulario de Productos
- `sql/limpiar_bd.sql` creado: script de DROP de todas las tablas
  en orden seguro, para uso en desarrollo
- Migración ejecutada sin pérdida: base de datos recreada desde cero
  (solo existía el usuario admin de prueba), `seed_admin.py` volvió
  a correr para recrear el admin
- `db.py` actualizado: `get_productos()` trae `codigo_producto` real
  del SELECT; búsqueda simplificada — compara directo contra
  `codigo_producto` con `ILIKE` sin necesidad de parsear el prefijo
- `productos.py` actualizado: tabla Consultar muestra
  `p["codigo_producto"]` (dato real de BD) en vez de
  `f"PRD-{id:04d}"` construido en pantalla

### Sesión 13 — Pulido visual: contraste de inputs, íconos y flujo de sesión

- Bug resuelto: texto invisible en inputs de Productos y login —
  causa raíz: los campos heredan el fondo navy oscuro de `.stApp`
  (no de la tarjeta blanca contenedora como se asumía). Diagnóstico
  confirmado con el inspector (Calculada → background-color).
  Solución: `color: #FFFFFF` en ambos contextos (login en `auth.py`,
  módulos en `main.py`)
- Lección documentada: cuando un cambio de CSS "funciona" pero el
  resultado no tiene lógica con lo que se cambió, es señal de
  diagnóstico incorrecto — confirmar background-color real con el
  inspector antes de iterar, no después de 2-3 intentos fallidos
- Bug resuelto: ícono del ojo (mostrar/ocultar contraseña) invisible
  en el login — mismo problema de contraste (ícono navy sobre fondo
  navy). Solución: `.stTextInput button svg { fill: #FFFFFF !important; }`
- Bug resuelto: al cerrar sesión y volver a entrar, el ERP recordaba
  el último módulo visitado en vez de arrancar en Inicio. Causa:
  `cerrar_sesion()` no reseteaba `pagina_actual`. Solución:
  `st.session_state.pagina_actual = "inicio"` agregado en
  `cerrar_sesion()`
- Mejora: scroll reset al cerrar sesión —
  `window.scrollTo(0, 0)` vía `st.markdown` para evitar que el login
  aparezca desplazado hacia abajo
- CSS global de `main.py` consolidado y limpiado: selector CSS
  redundante de `stSelectbox` eliminado (el selector más específico
  `div[data-baseweb="select"] div` ya cubría todo lo que hacía el
  más general)
- Decisión de pricing definida (PM + Joey): modelo de add-ons sobre
  plan base — módulos especializados (Producción, FEL, Nómina) se
  cobran aparte. Regla: si el 80% de clientes daría por hecho que
  viene incluido → core. Si es nicho-específico → add-on
- Implicación técnica a futuro: `config_empresa` debería guardar
  qué módulos tiene activos cada cliente, para que activar un
  módulo nuevo sea un flag, no una rama de código separada
- Reorganización del sidebar pendiente de implementar: grupo
  "INVENTARIO" dividir en "INVENTARIO" (solo `inventarios`) y
  nuevo grupo "REPORTES" (Dashboard Comercial + Dashboard Financiero)
  — Dashboard no es un módulo operativo, es un reporte de solo
  lectura, y no debe mezclarse con el módulo de gestión de stock

### Estado actual del proyecto (post Sesión 13)

**Archivos en estado limpio y auditado:**
- `app/auth.py` — login completo, ícono del ojo visible, scroll reset
- `app/db.py` — conexión, autenticación, config, catálogos, Productos
- `app/main.py` — sidebar, home, enrutamiento, CSS global consolidado
- `app/pages/productos.py` — primer maestro completo y funcional
- `sql/leerp_schema.sql` — v1.1 con códigos, auditoría y Kardex
- `sql/limpiar_bd.sql` — script de limpieza para desarrollo

**Pendientes inmediatos antes de construir el próximo módulo:**
1. Cargar categorías de prueba en DBeaver (`INSERT INTO categoria ...`)
   para poder registrar el primer producto real
2. Implementar el reset visual del formulario al cancelar (patrón de
   `key` dinámica en `st.form`)
3. Revisar `color="currentColor"` en `iconos.py` (pendiente de Sesión 9)
4. Implementar reorganización del sidebar (REPORTES separado de INVENTARIO)

### Sesión 14 — Pruebas integrales del módulo Productos y correcciones
 
- Pruebas realizadas desde cero: login → sidebar → módulo Productos →
  carga de productos reales (tienda de tecnología) → Consultar con filtros
- 7 de 10 puntos del reporte de pruebas resueltos en la primera ronda
#### Bugs resueltos
 
- **Cursor invisible en inputs** (login y módulos): `caret-color: #FFFFFF`
  agregado al CSS de `auth.py` y `main.py`
- **Texto superpuesto en input Precio**: causa raíz — `color-scheme: light`
  inyectado por Streamlit hacía que el navegador pusiera sus propios estilos
  encima del CSS del proyecto. Solución: `.stNumberInput input
  { color-scheme: dark !important; }` en CSS global de `main.py`
- **Placeholder campo Nombre**: generalizado de "Ej. Monitor 4K 27 pulgadas"
  a "Ej. Laptop, Mouse, Servicio técnico..." — aplica a cualquier cliente
- **Campo Costo agregado al formulario**: pendiente técnico desde Sesión 12
  (cuando se guardaba `0.0` temporal). Formulario ahora tiene 4 columnas
  en segunda fila: Tipo | Unidad | Costo | Precio de venta.
  Margen de utilidad (`precio - costo`) queda en BD para el Dashboard
- **`get_producto_by_id()`** en `db.py` actualizado para incluir
  `codigo_producto` en el SELECT — necesario para el mensaje de éxito
  al editar
#### Comportamientos confirmados normales (no bugs)
 
- Delay en operaciones: latencia de red a Neon Cloud. Solución futura:
  `@st.cache_data` en catálogos. No urgente para ≤5 usuarios
- Scroll al llegar al home post-login: timing issue menor, pendiente bajo
#### Validaciones probadas y funcionando ✅
 
- Guardar sin nombre → error, no guarda
- Filtros de Consultar (nombre, categoría, estado)
- Editar producto → cambio confirmado en DBeaver
- Mensaje de éxito con `codigo_producto` (ej. PRD-0001)
- Formulario limpio después de guardar y cancelar
#### Pendientes menores
 
- Botón "Editar" en tabla Consultar visualmente cortado (`Edi / tar`)
- Scroll al hacer login (timing issue)
- `color="currentColor"` en `iconos.py` (desde Sesión 9)
- Reorganización sidebar: grupo "REPORTES" separado de "INVENTARIO"
### Estado actual (post Sesión 14)
 
### Sesión 15 — Mejoras al módulo Productos: UX, rendimiento y auditoría
 
#### Arquitectura de navegación — eliminación de st.tabs()
 
- `st.tabs()` reemplazado por condicional explícito con `producto_vista`
  en `session_state` — valores: `"formulario"` | `"consultar"`
- Razón: `st.tabs` no permite seleccionar una pestaña programáticamente,
  causando comportamiento inconsistente al dar clic en "Editar" (a veces
  hacía scroll al formulario, a veces no, dependiendo de la posición del
  scroll en ese momento)
- Solución: dos botones de navegación (`Nuevo registro` / `Consultar`)
  con estado visual — botón activo en teal `primary`, inactivo en
  `secondary`. Al dar clic en "Editar" desde la tabla, se setea
  `producto_vista = "formulario"` de forma determinista antes del rerun
- Beneficio adicional: `product_editando` se limpia al cerrar sesión
  (agregado en `auth.py → cerrar_sesion()`) — el estado de edición
  ya no persiste entre sesiones
#### Limpieza de código
 
- Emojis eliminados de los botones de navegación — decisión de marca:
  LEERP es un producto TEC profesional, sin emojis en la interfaz
- Selector CSS redundante de `stSelectbox` eliminado de `main.py`
#### Vista Consultar — mejoras de UX y rendimiento
 
- **Búsqueda bajo demanda**: la tabla ya no muestra el universo completo
  al entrar a Consultar. Se muestra el mensaje "Configura los filtros
  y presiona Buscar" hasta que el usuario ejecute una búsqueda explícita.
  Beneficio: rendimiento mejorado (no se consulta la BD al entrar) y
  UX más limpia para catálogos grandes
- **Botón "Buscar"** agregado como cuarto elemento en la misma fila de
  filtros — proporciones finales: `[1.5, 1.2, 1.2, 0.7]`. El botón
  se alinea verticalmente con los inputs mediante `padding-top: 28px`
- **Columna "Costo"** agregada a la tabla de resultados — campos de
  `db.get_productos()` ampliados para incluir `p.costo`
- **Descarga CSV** implementada con `st.download_button` y `pandas`.
  El CSV incluye campos operativos + campos de auditoría:
  `Fecha creación` y `Creado por` (JOIN con tabla `usuarios`).
  Decisión de estándar: todos los CSV de LEERP incluirán siempre
  estos campos de auditoría — no como opción sino como parte del
  archivo base. Patrón a replicar en Ventas, Compras y demás módulos
- Separación visual entre filas de la tabla con CSS:
  `border-bottom: 0.5px solid rgba(0,0,0,0.06)` y padding vertical —
  sin cambios en Python, solo CSS en `main.py`
#### Cambios en db.py — get_productos()
 
- SELECT ampliado: agrega `p.costo`, `p.fecha_creacion`,
  `us.nombre_completo` (via LEFT JOIN con `usuarios`)
- Diccionario de retorno ampliado: nuevos campos `costo`,
  `fecha_creacion` (formateada como `YYYY-MM-DD HH:MM`), `creado_por`
#### Reorganización del sidebar
 
- Grupo `INVENTARIO` ahora contiene solo `inventarios` (módulo operativo)
- Nuevo grupo `REPORTES` creado con dos items:
  - `dashboard_comercial` → "Comercial"
  - `dashboard_financiero` → "Financiero"
- `COLOR_GRUPO` en `navegacion.py` actualizado con color para `REPORTES`:
  `{"bg": "#F4EDF8", "icon": "#7B4FA6"}`
- Íconos para ambos dashboards agregados en `iconos.py`
- `permisos.py` actualizado con las nuevas keys para que
  `menu_visible()` las incluya en el sidebar
#### Decisiones de diseño confirmadas
 
- Tabla con bordes visuales (HTML crudo): descartado por costo/beneficio
  desfavorable en Streamlit. El separador CSS es suficiente
- Scroll automático al home post-login: descartado definitivamente —
  timing issue irresoluble con `window.scrollTo` en Streamlit
- Filtro de fecha en Consultar: anotado para módulos transaccionales
  (Ventas, Compras, Gastos) — no aplica en maestros
### Estado actual (post Sesión 15)
 
**Módulo Productos: COMPLETO Y CERRADO ✅**
 
Archivos modificados en esta sesión:
- `app/pages/productos.py` — navegación por condicional, Buscar,
  Costo en tabla, CSV con auditoría
- `app/db.py` — `get_productos()` con costo y auditoría
- `app/main.py` — CSS separador de filas, limpieza de selectores
- `app/auth.py` — limpieza de session_state al cerrar sesión
- `utils/navegacion.py` — grupo REPORTES, split de INVENTARIO
- `utils/iconos.py` — íconos dashboard_comercial y dashboard_financiero
- `utils/permisos.py` — nuevas keys de dashboards

### Sesión 16 — Cierre del módulo Productos
 
#### Cambios estructurales
 
- `st.data_editor` con checkbox descartado definitivamente — el callback
  `on_change` resolvía el timing issue pero la experiencia visual no
  mejoraba respecto al problema original. Decisión: tres vistas
  separadas (Nuevo registro / Consultar / Modificar) en vez de edición
  desde la tabla. Patrón estándar SAP/Odoo: búsqueda explícita → edición
- Formulario extraído a función `_formulario()` reutilizada por
  "Nuevo registro" y "Modificar" — cambios futuros al formulario
  se hacen en un solo lugar
- Botón "Guardar producto" centrado con columnas `[2, 3, 2]` —
  ya no ocupa todo el ancho de pantalla
#### Vista Modificar — decisiones de diseño
 
- Búsqueda por código del producto (campo de texto libre + botón Buscar)
- Si encuentra 1 resultado → carga formulario precargado con `st.rerun()`
  inmediato (sin esto, Streamlit no actualizaba la vista en ese ciclo)
- Si no encuentra resultado → limpia `producto_editando = None` para
  que el formulario anterior desaparezca. Razón: usuario mecánico
  puede no revisar qué producto está editando si el formulario
  permanece visible de una búsqueda anterior
- Si encuentra más de 1 resultado → warning pidiendo código exacto
- Búsqueda acepta código parcial (ej. `0007` encuentra `PRD-0007`) —
  comportamiento intencional, más ágil para el usuario operativo
- Label cambiado a "Ingrese el código del producto" — comunica
  claramente que se espera un código, no texto libre
- Función `get_producto_by_codigo()` agregada a `db.py` — búsqueda
  exacta por `codigo_producto` con `RealDictCursor`
#### Mejora de `db.py` — RealDictCursor
 
- Todas las funciones de consulta migradas a `RealDictCursor`
  (`psycopg2.extras`): cada fila es un dict con nombres de columna
  como llaves (`r["nombre"]` en vez de `r[3]`)
- Elimina permanentemente el riesgo de `KeyError` por índices
  desincronizados al agregar columnas al SELECT
- `verificar_login` mantiene cursor estándar — necesita `row[2]`
  para bcrypt antes de construir el dict
- `insert_producto` y `update_producto` mantienen cursor estándar —
  no leen filas, solo escriben
#### Archivos modificados en esta sesión
 
- `app/pages/productos.py` — tres vistas, formulario reutilizable,
  reset de módulo, Modificar con búsqueda exacta
- `app/db.py` — RealDictCursor en todas las consultas,
  nueva función `get_producto_by_codigo()`
### Estado actual (post Sesión 16)
 
### Sesión 17 — Módulos Proveedores e Insumos + FEL + Roadmap

#### Módulo Proveedores — COMPLETO

- Mismo patrón de 3 vistas que Clientes (Nuevo / Consultar / Modificar)
- Campo adicional respecto a Clientes: `contacto` (nombre de la persona
  de contacto en el proveedor)
- Búsqueda en Modificar acepta código parcial (ILIKE) —
  homologado con el comportamiento de Productos y Clientes
- Archivos afectados: `proveedores.py` (nuevo), `db.py` (5 funciones
  agregadas), `main.py` (import + MODULOS), `auth.py` (keys de limpieza)

#### Módulo Insumos — COMPLETO

- Diferencias respecto a otros maestros:
  - Sin categoría (solo unidad de medida)
  - Sin precio de venta — solo costo de adquisición
  - `activo` y `costo` en la misma fila del formulario (menos campos,
    mejor uso del espacio)
- Búsqueda en Consultar por nombre o código
- Mismo patrón de limpieza de `session_state` al cerrar sesión
- Archivos afectados: `insumos.py` (nuevo), `db.py` (6 funciones
  agregadas), `main.py` (import + MODULOS), `auth.py` (keys de limpieza)

#### Consulta técnica — FEL (Factura Electrónica en Línea SAT Guatemala)

- Confirmado que es técnicamente viable a través de certificadores
  autorizados (INFILE, Megaprint, G4S, entre otros)
- El SAT no tiene API pública directa — la integración es vía
  certificador (intermediario homologado)
- Costo por documento: aprox. Q0.10–Q0.50 según volumen y certificador
- En Guatemala la FEL es obligatoria para la mayoría de contribuyentes
- Decisión: FEL va en la Capa 2 de add-ons (cobro aparte), no en el
  core del ERP base
- Acción inmediata: el módulo de Ventas se diseñará FEL-ready —
  campos necesarios (NIT cliente, descripción de línea, cantidad,
  precio unitario, total) incluidos desde el diseño base. La capa
  de integración con el certificador se agrega después como módulo
  independiente

#### Estado de los 4 maestros

| Módulo | Estado |
|---|---|
| Productos | COMPLETO |
| Clientes | COMPLETO |
| Proveedores | COMPLETO |
| Insumos | COMPLETO |

#### Roadmap definido — próximas etapas

1. **Ventas** — prioridad máxima, módulo de mayor valor para demo
   comercial. Complejidad nueva: cabecera + detalle (múltiples líneas).
   Requiere diseño de UX previo antes de codificar
2. **Compras** — mismo patrón cabecera/detalle, genera `entrada_compra`
   en Kardex
3. **Gastos** — más simple, sin movimiento de inventario de productos
4. **Inventarios** — vista de consulta del Kardex + ajustes manuales
5. **Configuración** — gestión de `config_empresa`, categorías,
   unidades de medida (actualmente via DBeaver)
6. **Usuarios** — CRUD solo para rol `admin`
7. **Dashboards** — Comercial y Financiero, al final cuando haya
   datos transaccionales

#### Próxima sesión — diseño de Ventas

Antes de codificar, definir:
- Cómo manejar el detalle (múltiples líneas de producto) en Streamlit
- Cómo el Kardex recibe el movimiento automático al guardar la venta
- Campos mínimos para ser FEL-ready desde el día 1

### Sesión 18 — Módulo Ventas (construcción, depuración y consulta transaccional)

#### Módulo Ventas — construcción inicial

- `app/pages/ventas.py` creado: patrón de 2 pasos en vez del patrón de
  3 vistas usado en los maestros — complejidad nueva (cabecera +
  múltiples líneas de detalle) no encajaba en el patrón anterior
  - Paso 1: datos de cabecera — tipo de cliente (Consumidor Final /
    Cliente registrado / Buscar por NIT), fecha de venta
  - Paso 2: líneas de detalle — búsqueda de producto tipo-ahead (mismo
    patrón de búsqueda por nombre/código ya usado en Clientes),
    cantidad, precio editable, tabla acumulada de líneas con opción de
    eliminar antes de guardar
- Validación agregada: no permite agregar el mismo producto dos veces
  en una venta (evita líneas duplicadas — el usuario debe editar
  cantidad en la línea existente)
- Opción "Buscar por NIT (FEL)" dejada como placeholder deshabilitado
  — mensaje "Módulo FEL disponible próximamente" — consistente con la
  decisión de Sesión 17 (FEL es Capa 2, add-on aparte)
- `venta_cabecera` / `venta_detalle` ya existían en `leerp_schema.sql`
  (v1.1) — no fue necesario modificar el esquema para esta sesión

#### Bug — `KeyError: 'total'` en Consultar

- Causa raíz diagnosticada: `get_ventas()` en `db.py` devolvía cada
  fila con la llave `total_venta`, pero `ventas.py` leía `v['total']`
  — nombres desincronizados entre la query y la vista
- Hallazgo más importante detrás del mismo bug: la query original unía
  `venta_detalle` dos veces (`d` y `d2`) para calcular el total con
  `SUM() OVER (PARTITION BY ...)` — esto generaba un producto
  cartesiano en ventas con más de una línea (N líneas × N líneas antes
  de la ventana), inflando el número de filas devueltas de forma
  silenciosa
- Fix: `get_ventas()` reescrita — un solo `JOIN` a `venta_detalle` +
  subquery aparte (`GROUP BY id_venta`) para el total por venta, sin
  self-join. Elimina el cartesiano y corrige el nombre de la llave

#### Decisión pendiente cerrada — campos de la consulta transaccional

- Se identificó que la Sesión 17 dejó pendiente ("próxima sesión —
  diseño de Ventas") la definición formal de campos para Consultar, y
  nunca se completó antes de empezar a codificar — laguna de proceso
  detectada y corregida en esta sesión
- Campos definidos para que Consultar sirva de base a futuros
  dashboards (Comercial / Financiero), no solo como pantalla de
  revisión:
  - Cliente + NIT (FEL-ready, decisión Sesión 17)
  - Producto + Categoría (categoría controlada = agrupación BI,
    decisión Sesión 2)
  - Cantidad, Precio unitario, Subtotal
  - Costo, Margen (decisión Sesión 14: el margen vive en BD para el
    Dashboard Financiero)
  - Total de venta, Estado (Activa/Anulada), Registrado por
- **Limitación conocida, sin resolver:** el margen se calcula con el
  `producto.costo` **actual**, no con el costo real al momento de la
  venta — `venta_detalle` no guarda un snapshot de costo (a diferencia
  de `compra_detalle`, que sí guarda `costo_unitario` histórico).
  Pendiente evaluar si se agrega `costo_unitario` a `venta_detalle`
  antes de construir el Dashboard Financiero, para márgenes históricos
  exactos

#### Iteración de diseño — vista Consultar

- Primer intento: resumen de cabecera (una fila por venta) +
  `st.expander` por venta con el detalle de líneas — descartado:
  no escala para revisar visualmente muchas transacciones (ej. 100
  ventas en un mes = 100 clics), aunque el CSV de descarga ya era
  una sola descarga para todo el rango, no por venta
- Segundo intento: `st.radio` para alternar entre "Resumen por venta"
  y "Detalle completo" (tabla plana) — descartado: el radio no
  aportaba suficiente valor sobre solo mostrar el detalle, y además
  causó un bug (ver abajo)
- **Diseño final:** una sola tabla plana, grano de línea de producto
  (una fila por producto vendido, todas las ventas del rango juntas),
  ordenable por columna con clic — mismo shape que el CSV de
  descarga. Referencia de patrón: listados transaccionales tipo SAP
  (`VA05`) — tabla plana en vez de jerarquías visuales
- Concepto BI aplicado: esta tabla es la "tabla de hechos" (*fact
  table*) de Ventas — el mismo shape que va a leer el futuro Dashboard
  Comercial/Financiero sin necesidad de rehacer la query

#### Bug — resultados desaparecen al interactuar con otros controles

- Causa raíz: la búsqueda dependía únicamente de `st.button("Buscar")`,
  cuyo estado es transitorio (`True` solo en el render inmediato al
  clic). Cualquier otro widget de la página (el `st.radio` del intento
  anterior, o incluso el botón de descarga CSV) dispara un rerun de
  Streamlit, y en ese rerun `buscar` vuelve a `False` — la función
  regresaba al mensaje "Configura los filtros y presiona Buscar",
  borrando visualmente los resultados ya obtenidos
- Fix: resultados de la búsqueda guardados en
  `st.session_state.vta_resultados`, ya no dependen del estado
  transitorio del botón. Se limpia al reingresar al módulo (mismo
  patrón de reset ya usado para las demás llaves de sesión)

#### Validado en pruebas

- 2 ingresos de prueba realizados directamente en el ERP (sin datos
  semilla — Chandler ingresando como usuario real para detectar bugs,
  igual que en los demás maestros)
- Consulta y descarga de CSV confirmadas funcionando correctamente
  después de los fixes

#### Archivos modificados en esta sesión

- `app/pages/ventas.py` — creado y luego iterado varias veces
  (Paso 1 y Paso 2 estables desde la primera versión; Consultar
  rediseñada tres veces hasta la tabla plana final)
- `app/db.py` — `get_ventas()` reescrita: grano de línea, sin
  producto cartesiano, con cliente/NIT, categoría, costo y margen

#### Pendiente para próximas sesiones

1. Conectar el guardado de una venta con `movimiento_inventario`
   (`tipo_movimiento = 'salida_venta'`) — actualmente `insert_venta()`
   guarda la transacción pero no se confirmó si ya descuenta stock
   vía Kardex
2. UI de anulación de venta (`anulada`, `motivo_anulacion` ya existen
   en el esquema desde v1.1, falta la pantalla/flujo)
3. Evaluar `costo_unitario` histórico en `venta_detalle` para margen
   exacto (ver limitación arriba)
4. Mejora menor de UX: mover el botón de descarga CSV más arriba,
   cerca de los filtros, para que sea más visible
5. Con Ventas estabilizado, continuar con **Compras** (mismo patrón
   cabecera/detalle, según roadmap de Sesión 17)

### Estado actual (post Sesión 18)

| Módulo | Estado |
|---|---|
| Productos | COMPLETO |
| Clientes | COMPLETO |
| Proveedores | COMPLETO |
| Insumos | COMPLETO |
| Ventas | EN PROGRESO — alta y consulta funcionales; falta Kardex automático y anulación |

A partir de esta sesión, la bitácora se actualiza de forma incremental
(solo los avances de cada sesión nueva se agregan al final del
documento).