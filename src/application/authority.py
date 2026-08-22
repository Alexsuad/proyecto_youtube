"""Strict reader for the live operational authority block."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

import yaml


class OperationalAuthorityError(PermissionError):
    """The live authority cannot be resolved safely."""


@dataclass(frozen=True)
class OperationalAuthority:
    section: str
    values: dict[str, Any]


class _UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_unique_mapping(loader: _UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise OperationalAuthorityError(f"Clave duplicada en autoridad canónica: {key}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


REQUIRED_VALUES = {
    "R1_GATE": {"PASS", "FAIL", "BLOCKED"},
    "R2_CONTROLLED_EXECUTION": {"AUTHORIZED", "REVOKED", "NOT_AUTHORIZED"},
    "R2_SCOPE": {"B5_I1_CONTROLLED_EXECUTION", "NONE"},
    "R2_STATUS": {"AUTHORIZED_CONTROLLED_B5_I1_NOT_EXECUTED", "REVOKED", "NOT_AUTHORIZED"},
    "B5_I3": {"AUTHORIZED", "REVOKED", "NOT_AUTHORIZED"},
    "S5_REAL_EXECUTION": {"AUTHORIZED", "BLOCKED", "REVOKED"},
}

EXPECTED_FOR_CONTROLLED_B5_I1 = {
    "R1_GATE": "PASS",
    "R2_CONTROLLED_EXECUTION": "AUTHORIZED",
    "R2_SCOPE": "B5_I1_CONTROLLED_EXECUTION",
    "R2_STATUS": "AUTHORIZED_CONTROLLED_B5_I1_NOT_EXECUTED",
    "B5_I3": "NOT_AUTHORIZED",
    "S5_REAL_EXECUTION": "BLOCKED",
}


def _canonical_section(document: str) -> str:
    headings = list(re.finditer(r"^##[ \t]+(.+?)[ \t]*$", document, re.MULTILINE))
    matches = [match for match in headings if match.group(1).strip() == "1. Estado canónico"]
    if len(matches) != 1:
        raise OperationalAuthorityError("La sección canónica debe existir una sola vez.")
    heading = matches[0]
    following = next((match for match in headings if match.start() > heading.end()), None)
    return document[heading.end() : following.start() if following else len(document)]


def resolve_operational_authority(document: str) -> OperationalAuthority:
    section = _canonical_section(document)
    blocks = list(
        re.finditer(
            r"^```yaml[ \t]*\r?\n(.*?)^```[ \t]*\r?$",
            section,
            re.MULTILINE | re.DOTALL,
        )
    )
    if len(blocks) != 1:
        raise OperationalAuthorityError("La sección canónica debe contener un único bloque yaml.")
    try:
        values = yaml.load(blocks[0].group(1), Loader=_UniqueKeyLoader)
    except OperationalAuthorityError:
        raise
    except yaml.YAMLError as exc:
        raise OperationalAuthorityError(f"Estado canónico malformado: {exc}") from exc
    if not isinstance(values, dict):
        raise OperationalAuthorityError("El bloque canónico debe resolver a un objeto.")
    for key, allowed in REQUIRED_VALUES.items():
        if key not in values:
            raise OperationalAuthorityError(f"Clave canónica ausente: {key}")
        if values[key] not in allowed:
            raise OperationalAuthorityError(f"Valor canónico no reconocido para {key}: {values[key]!r}")
    mismatches = [
        f"{key}={values.get(key)!r} (requiere {expected!r})"
        for key, expected in EXPECTED_FOR_CONTROLLED_B5_I1.items()
        if values.get(key) != expected
    ]
    if mismatches:
        raise OperationalAuthorityError("Ejecución controlada no autorizada: " + "; ".join(mismatches))
    return OperationalAuthority("1. Estado canónico", values)


def load_operational_authority(path) -> OperationalAuthority:
    try:
        document = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise OperationalAuthorityError("No se pudo leer la autoridad operativa.") from exc
    return resolve_operational_authority(document)
