-- ==================================================================
-- LEERP — Agregar campo 'id_usuario_creacion' en las tablas master
-- Implementación propuesta por el equipo de asesores externos
-- ==================================================================
ALTER TABLE producto ADD COLUMN id_usuario_creacion INT REFERENCES usuarios(id_usuario);
ALTER TABLE cliente ADD COLUMN id_usuario_creacion INT REFERENCES usuarios(id_usuario);
ALTER TABLE proveedor ADD COLUMN id_usuario_creacion INT REFERENCES usuarios(id_usuario);
ALTER TABLE insumo ADD COLUMN id_usuario_creacion INT REFERENCES usuarios(id_usuario);

select * from producto;
select * from cliente;
select * from proveedor;
select * from insumo;