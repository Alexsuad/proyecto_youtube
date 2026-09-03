# B1 — Contratos y frontera Research → Narrative

## Estado

```text
B1_STATUS = CLOSED
M1_STATUS = CLOSED_OWNER_APPROVED
M2_STATUS = CLOSED_OWNER_APPROVED
M3_STATUS = NOT_AUTHORIZED
M2_EXECUTION = CLOSED
IMPLEMENTATION = NOT_AUTHORIZED
```

B1, M1 y M2 quedan materializados, ejecutados y cerrados con aprobación del
OWNER. El informe bajo `m1_inventory_design/` y los contratos bajo
`m2_contracts_boundary/` son los registros canónicos de ese trabajo. M3 sigue
sin autorización.

## Alcance

B1 establece la base contractual del Sistema de Investigación V2 dentro del sistema existente. Se aplican, en este orden:

```text
SEARCH BEFORE CREATE
REUSE → EXTEND → CREATE
SOFTWARE → IA → SOFTWARE
```

No se crea un segundo sistema, ledger, dossier, runtime, autorización, storage, provenance o lifecycle general. La decisión de crear cualquier artefacto queda condicionada a una brecha real demostrada.

## M1 — Inventario y diseño antes de crear

M1 produjo evidencia suficiente para decidir:

- inventario `SEARCH BEFORE CREATE` y matriz `REUSE / EXTEND / MOVE-RECONCILE / CREATE_ONLY_IF_GAP`;
- matriz de estados ortogonales, separando como mínimo `research_stage`, `selection_state`, `preliminary_fidelity`, `deep_fidelity`, `research_sufficiency`, `artifact_validity` y `thesis_stage`;
- transiciones, invalidaciones y owners sin mega-enum cartesiano;
- mapa de responsabilidades cognitivas por rol y unidad concreta (`skill`, `prompt` o `capability`), incluyendo brechas demostradas;
- inventario del consumer contract `Research V2 → B5-I3`, con inputs, outputs, restricciones, lineage y dependencias actuales;
- gaps reales y decisiones sobre qué se reutiliza, extiende, mueve/reconcilia o crea solo si no existe una pieza suficiente.

M1 no modificó contratos de producto, código, schemas, prompts, skills, agentes,
capabilities, CLI, harness ni tests.

## M2 — Implementación contractual mínima y frontera

M2 se ejecutó después del cierre y revisión de M1, con autorización específica
del OWNER. Su alcance fue exclusivamente materializar los contratos V2 que M1
demostró necesarios, reconciliar los existentes y formalizar:

- frontera `Research → B5-I3`;
- compatibilidad y versionado explícitos, mediante adaptador o migración cuando corresponda;
- bindings, provenance y lineage verificables;
- separación estructural `WORK / NARRATIVE EVIDENCE ≠ EXTERNAL REALITY EVIDENCE`;
- restricciones downstream sin trasladar decisiones narrativas a Research.

## Frontera de responsabilidades

```text
RESEARCH
→ determina qué sabemos,
  evidencia,
  claims,
  fidelidad,
  rivales,
  límites,
  tesis defendible.

B5-I3
→ decide viewer journey,
  arquitectura,
  orden,
  hook,
  bloques,
  ritmo,
  clímax,
  cierre.
```

El handoff debe entregar conocimiento investigado, evidencia y restricciones trazables, sin convertir Research en autor de la arquitectura narrativa.

## Outputs esperados y cierre

La materialización y ejecución de B1 produjeron este documento, el informe M1
y los contratos y validaciones de M2. El estado vivo queda reconciliado sin
cambiar `CURRENT_MISSION` ni `CURRENT_MISSION_EXECUTION_BUNDLE`. M1 y M2 están
cerradas y aprobadas por el OWNER.

El cierre de B1 se sustenta en el inventario de M1 cerrado, la matriz de
estados ortogonales, el mapa de responsabilidades cognitivas, el
consumer-contract de `Research V2 → B5-I3`, los gaps reales, la frontera
formalizada, la compatibilidad explícita y la revisión requerida. Este cierre
no autoriza automáticamente M3, B2 ni ninguna ejecución productiva.

```text
REAL_AI = NO
PRODUCT_USE = NO
P2_REAL = NO
B5_5 = NO
B6 = NO
B7 = NO
COMMIT = NO
PUSH = NO
```
