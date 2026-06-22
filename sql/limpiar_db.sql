-- ============================================================
-- LEERP — limpiar_bd.sql
-- Elimina todas las tablas del esquema, en orden seguro respecto
-- a sus dependencias (CASCADE se encarga del resto).
--
-- USO: solo en desarrollo / antes de tener datos reales de cliente.
-- Después de correr este script, hay que volver a ejecutar
-- leerp_schema.sql y luego scripts/seed_admin.py para tener un
-- usuario admin con el que hacer login de nuevo.
-- ============================================================

DROP TABLE IF EXISTS gasto_detalle CASCADE;
DROP TABLE IF EXISTS gasto_cabecera CASCADE;
DROP TABLE IF EXISTS compra_detalle CASCADE;
DROP TABLE IF EXISTS compra_cabecera CASCADE;
DROP TABLE IF EXISTS venta_detalle CASCADE;
DROP TABLE IF EXISTS venta_cabecera CASCADE;
DROP TABLE IF EXISTS movimiento_inventario CASCADE;
-- DROP TABLE IF EXISTS inventario_inicial CASCADE; -- Tabla de la versión 1.0
DROP TABLE IF EXISTS insumo CASCADE;
DROP TABLE IF EXISTS proveedor CASCADE;
DROP TABLE IF EXISTS cliente CASCADE;
DROP TABLE IF EXISTS producto CASCADE;
DROP TABLE IF EXISTS categoria CASCADE;
DROP TABLE IF EXISTS unidad_medida CASCADE;
DROP TABLE IF EXISTS usuarios CASCADE;
DROP TABLE IF EXISTS config_empresa CASCADE;