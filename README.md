# LEERP

Sistema ERP modular para micro y pequeñas empresas — ventas, compras,
inventario y gastos operativos, con autenticación por roles y reportería
integrada.

---

## Descripción

LEERP nace como evolución de **GuateCompost ERP**, un proyecto freelance
desarrollado para una distribuidora de productos de compostaje. A partir
de ese piloto —que funcionó bien pero estaba diseñado para un solo
cliente y sin pantalla de login— LEERP se generaliza en un producto
comercializable, replicable a cualquier micro o pequeña empresa que
necesite reemplazar el control manual en Excel por una herramienta
estructurada y segura.

GuateCompost queda como referencia histórica del aprendizaje (ver
`docs/bitacora.md`), pero LEERP se construye desde cero, corrigiendo
decisiones que en el piloto no se evaluaron a tiempo — la más importante,
la ausencia total de autenticación.

---

## Objetivos del proyecto

- Proveer un ERP liviano y configurable para micro y pequeñas empresas
- Resolver el vacío de seguridad del piloto: autenticación obligatoria
  con control de acceso por roles
- Mantener una arquitectura reutilizable: un mismo código base,
  desplegado en una instancia y base de datos aislada por cliente
- Aprovechar herramientas open-source y cloud serverless (Neon) para
  mantener bajo el costo operativo

---

## Modelo de despliegue

Cada cliente tiene:

- Su propio proyecto en **Neon** (PostgreSQL aislado — no hay datos
  compartidos entre clientes)
- Su propia instancia de la app (Streamlit Cloud u otro hosting)
- Configuración superficial vía la tabla `config_empresa`: nombre de
  la empresa, país, moneda (código ISO 4217) y logo

Se priorizó aislamiento y simplicidad sobre un modelo multi-tenant
compartido — válido mientras la base de clientes sea pequeña. Si el
volumen de clientes crece al punto de volver costoso mantener N
instancias en paralelo, este punto se revisita.

---

## Roles y permisos

| Rol | Acceso |
|---|---|
| `admin` | Total — incluye gestión de usuarios y configuración |
| `captura` | Ingreso de datos (maestros y transacciones) |
| `analista` | Ingreso de datos + consultas y reportes |
| `visor` | Solo consulta (dashboard, inventario) |

La matriz completa módulo × rol vive en `app/utils/permisos.py`.

---

## Stack tecnológico

| Capa | Herramienta |
|---|---|
| Lenguaje | Python 3 |
| Interfaz | Streamlit |
| Base de datos | PostgreSQL (Neon Cloud) |
| Autenticación | bcrypt (hash de contraseñas, nunca texto plano) |
| Reportería | Power BI / Looker Studio (conexión directa a PostgreSQL) |
| Control de versiones | Git / GitHub |

---

## Modelo de datos

Generalizado a partir de las 11 tablas de GuateCompost, con estos
cambios incorporados desde el diseño base (no como parches
posteriores):

- **`usuarios`** — login y roles
- **`config_empresa`** — datos configurables por cliente
- **`unidad_medida`**, **`categoria`** — catálogos controlados en vez
  de texto libre, para consistencia entre clientes
- **`activo`** y auditoría (`fecha_creacion`) como estándar en todo
  maestro
- **`producto.tipo`** distingue producto físico vs. servicio
- Trazabilidad: toda transacción (venta, compra, gasto) referencia
  `id_usuario` — quién la registró
- Montos en `NUMERIC(15,2)` — nunca `float` para dinero
- Fechas en tipo `DATE`/`TIMESTAMP` nativo de PostgreSQL

Esquema completo en [`sql/leerp_schema.sql`](sql/leerp_schema.sql).

---

## Estructura del proyecto

```
leerp/
├── app/
│   ├── main.py              # entrada, navegación, gate de login
│   ├── auth.py               # pantalla de login + verificación de sesión
│   ├── config.py             # carga .env, constantes
│   ├── db.py                 # capa de datos (conexión + queries)
│   ├── pages/
│   │   ├── productos.py
│   │   ├── clientes.py
│   │   ├── proveedores.py
│   │   ├── insumos.py
│   │   ├── ventas.py
│   │   ├── compras.py
│   │   ├── gastos.py
│   │   ├── inventarios.py
│   │   ├── dashboard.py
│   │   └── usuarios.py       # solo admin — CRUD de usuarios
│   └── utils/
│       ├── auth_utils.py     # hash_password / verificar_password
│       └── permisos.py       # matriz de roles
├── scripts/
│   └── seed_admin.py         # bootstrap del primer admin (1 vez por cliente)
├── sql/
│   ├── leerp_schema.sql
│   ├── datos_prueba.sql
│   └── limpiar_bd.sql
├── docs/
│   ├── erd.png
│   └── bitacora.md
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Configuración local (por cada cliente nuevo)

1. Clonar el repositorio
2. Crear entorno virtual: `python -m venv venv && source venv/bin/activate`
3. Instalar dependencias: `pip install -r requirements.txt`
4. Copiar `.env.example` a `.env` y completar credenciales del proyecto
   Neon de este cliente
5. Ejecutar `sql/leerp_schema.sql` contra esa base de datos
6. Crear el primer usuario admin: `python scripts/seed_admin.py`
7. Correr la app: `streamlit run app/main.py`

---

## Estado del proyecto

En desarrollo activo. El piloto GuateCompost ERP queda documentado en
`docs/bitacora.md` como bitácora de aprendizaje del proceso, no como
código base a mantener.

---

## Autor

Edwin Lee Tiño
