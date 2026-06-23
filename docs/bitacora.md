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
 
**Módulo Productos: completo y funcional ✅**
Listo para clonar en Clientes, Proveedores e Insumos.