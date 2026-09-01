# PLAN011 M1 — Pendiente externo

## Estado

`PLAN011_M1_B5_I1` queda cerrada y completada con evidencia sintética, revisión
OWNER aprobada y consolidación Git realizada. El siguiente defecto queda
registrado como preexistente y fuera del alcance autorizado de esta misión.

## Defecto

- Sede: `src/core/mission_completion_gate.py:643-662`.
- Causa de producción: `_normalize_path()` elimina el prefijo `./`, pero las
  comparaciones de protección no normalizan de forma consistente el valor
  declarado. `.agents/skills/tests-validacion-cierre/` se compara como
  `agents/skills/tests-validacion-cierre/`.
- Causa de escape: no existe un control dirigido que cubra una ruta protegida
  cuyo primer componente comience por punto.
- Clasificación: `PREEXISTENTE`, `OUT_OF_SCOPE_BY_DESIGN` para PLAN011 M1.
- Corrección: requiere una misión o ampliación de alcance separada; no se
  modifica este archivo aquí.

## Comprobación acotada

`run_mission_completion_gate()` ejecutado sobre el contrato de PLAN011 devuelve
únicamente:

```text
PROTECTED_UNTRACKED_INTEGRITY_FAILED
```

La discrepancia observada es la ruta normalizada
`agents/skills/tests-validacion-cierre/SKILL.md` con observación ausente. La
huella real del archivo `.agents/skills/tests-validacion-cierre/SKILL.md`
coincide con el baseline declarado:

```text
41cee8fb79b1b00ebd72b65c7088960f8f4a6a1c241444c481750127aef04334
```

La evidencia material de M1 no depende de ese control defectuoso: preflight,
schema, pruebas focales, regresiones autorizadas, ownership y binding de la
propuesta pasan determinísticamente. El defecto bloquea únicamente la sección
de integridad del artefacto protegido del gate común.
