# Skill — Investigación por cobertura

## Objetivo
Crear un `ResearchPack` trazable y suficiente para evaluar evidencia y formular
una tesis provisional, siguiendo el `ResearchPlan` aprobado.

## Frontera de responsabilidad
- Software asigna IDs, valida formato y procedencia, normaliza, deduplica,
  vincula cobertura, calcula checksums y persiste.
- La IA interpreta relevancia, contraste, relación con tesis, lectura rival y
  evaluación semántica; no inventa metadata, localizadores, estados de acceso ni
  checksums.
- La fuente, la persona o la IA pueden aportar contenido o referencias según el
  contrato, pero su procedencia debe conservarse.

## Modo B2 Research V2
Cuando el flujo indique la etapa B2 Research V2, esta skill se limita a la
investigación base y a sus salidas estructuradas: `ResearchPack`, discovery de
`WorkLifecycle`, `WorkResearchDossier`, `ResearchStopDecision`, tesis provisional
y comparativa investigativa. Puede evaluar aporte, cobertura, complementariedad,
redundancia, contraste, fidelidad, límites y evidencia.

El `ResearchPlan` aprobado es una entrada obligatoria y la guía metodológica de
B2. Antes de abrir búsquedas sustantivas, la cognición debe trabajar desde su
pregunta central, uso previsto, alcance, dimensiones, subpreguntas, evidencia
necesaria, estrategia de fuentes, claims críticos, hipótesis inicial,
rivales/refutación, gaps/riesgos, criterios de suficiencia y política de obras.
Si surge una dimensión, rival, contradicción o brecha material no prevista, debe
registrarla y reconsiderar el alcance afectado, sin cambiar silenciosamente la
pregunta de investigación.

En este modo no decide función narrativa, orden, progresión, viewer journey,
hook, pacing, clímax, cierre, CTA, título o thumbnail. `CurationDecision` no es
un requisito canónico de B2 V2; su uso histórico debe permanecer aislado en la
ruta legacy o en una adaptación explícita.

## Entradas
- `<EP_PATH>/episode_brief.json`;
- `<EP_PATH>/research_plan.json`;
- fuentes y materiales accesibles;
- políticas de fuentes del brief.

## Procedimiento
1. Leer el `ResearchPlan` y convertir sus líneas en preguntas de trabajo. La
   cobertura no se demuestra escribiendo texto: `COVERED` significa una respuesta
   suficientemente sustentada para el uso previsto en esta fase. Conservar
   `PARTIAL`, `PENDING` o `NOT_VERIFIABLE` cuando corresponda.
2. Investigar el fenómeno por cobertura profesional, según relevancia: significado
   preciso, pregunta, dimensiones, conceptos, evidencia importante, fuentes
   primarias/originales adecuadas, literatura especializada, datos, rivales,
   contradicciones, gaps, condiciones de aplicación, límites de generalización,
   confianza y qué no demuestra la evidencia. La hipótesis inicial es refutable.
3. Separar `DISCOVERY_POOL` del `BASE_RESEARCH_POOL`: hacer discovery amplio,
   filtrar primero por relación, versión, acceso razonable, redundancia y debilidad
   manifiesta, y reservar la investigación base profesional para el subconjunto que
   sobrevive. No imponer cuota rígida; `≈3 candidatas por plaza` es orientación de
   cobertura, no gate ni criterio de suficiencia. Las obras filtradas no requieren
   fidelidad preliminar.
4. Para cada obra superviviente, establecer antes de la fidelidad preliminar su
   identidad exacta y versión, autor/creador y año, contexto factual, personajes,
   conflicto, acontecimientos, decisiones y consecuencias relevantes. Documentar
   qué dimensión toca, por qué la relación es defendible, qué evidencia concreta
   la sostiene, qué aporta, qué repite, qué aporta diferencialmente, qué fue
   realmente consultado, calidad y límites, hechos frente a interpretación,
   sobreinterpretación, contradicciones, no verificado y limitaciones de acceso.
5. Evaluar la fidelidad preliminar solo después de esa base profesional, usando
   `APTA`, `APTA_CON_RIESGOS` o `NO_APTA`. La pregunta es si existe evidencia
   suficiente para recomendar responsablemente invertir investigación profunda, no
   si la obra simplemente parece relacionada.
6. Para cada claim material, preguntar qué se afirma exactamente y con qué fuerza.
   Ajustar la evidencia a su uso, fuerza, calidad, independencia, límites,
   condiciones de validez y rivales. La lista de tipos de claim es orientativa;
   no convertirla en score ni taxonomía universal. Mantener separadas asociación
   y causalidad, resultado contextual y generalización universal, e interpretación
   plausible e intención explícita.
7. Intentar encontrar evidencia que apoye, limite y contradiga la hipótesis, y
   buscar explicaciones rivales materiales antes de la tesis provisional. Una
   cantidad pequeña de fuentes muy adecuadas e independientes puede bastar para
   ciertos claims; muchas fuentes débiles, redundantes o inapropiadas pueden no
   bastar. Nunca decidir suficiencia por un número fijo.
8. Separar `NARRATIVE_EVIDENCE` (escena, pasaje, capítulo u otro elemento del
   medio) de `EXTERNAL_REALITY_EVIDENCE` (estudio, documento, dato, registro o
   análisis experto). Registrar solo evidencia realmente recuperada, accesos
   indirectos, límites y confianza; no fingir visionado ni acceso directo.
9. Emitir `ResearchStopDecision` por el ámbito real y formular la tesis provisional
   solo después de una decisión válida de suficiencia para ese ámbito. Mantenerla
   abierta a modificación y refutación. Después, registrar los targets que B3
   deberá profundizar: claims externos materiales, obras que requieren
   profundización y gaps, rivales o contradicciones pendientes. No hacer deep
   research en B2.
10. Comparar investigativamente por aporte, cobertura, complementariedad,
    redundancia, contraste, fidelidad, límites y evidencia. No seleccionar obras
    finales ni decidir función u orden narrativo.
11. Escribir y validar `<EP_PATH>/research_pack.json` y preparar
   `<EP_PATH>/source_access_and_evidence_report.json` para el gate canónico.

## Salidas
- `<EP_PATH>/research_pack.json`;
- `<EP_PATH>/source_access_and_evidence_report.json`.
- Discovery de `WorkLifecycle` y `BASE_RESEARCH_POOL` como salida estructurada de
  B2;
- `WorkResearchDossier` de las obras que sobreviven al filtro;
- `ResearchStopDecision` por el ámbito real investigado;
- tesis provisional posterior a una suficiencia válida;
- `ResearchComparison` investigativa, sin selección final ni función narrativa;
- targets de profundización para B3: claims externos materiales, obras que
  requieren profundización y gaps, rivales o contradicciones pendientes.

## Regla
La suficiencia depende del uso previsto, el claim, la fuerza del claim, la calidad,
la independencia, los límites y las explicaciones rivales; no de un número fijo de
fuentes. La evidencia de obra no es evidencia de realidad externa, y una fuente no
recuperada por Software no puede convertirse en evidencia consultada o verificada.
