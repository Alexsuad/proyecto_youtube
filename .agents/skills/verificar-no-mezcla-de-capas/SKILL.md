---
name: verificar-no-mezcla-de-capas
description: Revisa que autoridad, producto, ingeniería, evidencia y entrega permanezcan separados cuando una tarea cruza varias capas.
---

# Verificar no mezcla de capas

## Propósito

Identificar cruces que puedan confundir una decisión de autoridad, una implementación técnica, una capacidad funcional o una evidencia de cierre.

## Capas a distinguir

- autoridad viva, autorización de misión y aprobación funcional;
- contratos, schemas y runtime funcional/editorial;
- procedimiento de ingeniería, agentes y validadores;
- evidencia Git, tests y resultados de auditoría;
- entrega, activación, publicación o uso productivo.

## Procedimiento

1. Enumerar las capas implicadas por la instrucción.
2. Asignar cada archivo, acción y decisión a una sola capa principal.
3. Detectar si una evidencia técnica se está usando como aprobación funcional o autorización.
4. Detectar si un procedimiento está creando una capability, duplicando un gate o modificando el estado vivo.
5. Emitir el dictamen y la separación requerida antes de continuar.

## Salida

- `SIN_MEZCLA` cuando las fronteras están claras;
- `MEZCLA_CONTROLADA` cuando existe un cruce explícito y acotado;
- `MEZCLA_CRITICA` cuando una capa pretende ejercer autoridad de otra;
- `SEPARAR_TAREA` cuando el alcance debe dividirse.

## Límites

- No decidir requisitos funcionales o de negocio.
- No abrir ni cerrar gates.
- No modificar la entrega para ocultar una mezcla.
- No confundir revisión técnica, aprobación funcional y autorización de ejecución.
