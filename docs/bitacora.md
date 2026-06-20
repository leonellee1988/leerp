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