"""Strict reader for the live operational authority block."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

import yaml

from src.core.mission_authorization import MissionAuthorizationError, load_mission_authorization
from src.core.mission_completion_gate import load_mission_contract


class OperationalAuthorityError(PermissionError):
    """The live authority cannot be resolved safely."""


@dataclass(frozen=True)
class OperationalAuthority:
    section: str
    values: dict[str, Any]


@dataclass(frozen=True)
class ActiveMissionBundle:
    """The minimum execution bundle resolved from the active authority."""

    mission_id: str
    mission_contract_path: str
    mission_authorization_path: str


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


def _repository_reference(root: Path, reference: str, label: str) -> Path:
    candidate = Path(reference)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise OperationalAuthorityError(f"{label}: path outside repository")
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise OperationalAuthorityError(f"{label}: path outside repository") from exc
    return resolved


def resolve_active_mission_bundle(
    authority_path: str | Path,
    *,
    repository_root: str | Path,
) -> ActiveMissionBundle:
    """Resolve one explicit contract pointer for the active mission.

    The authority owns the pointer; mission names are never converted into
    filesystem paths by convention.  The contract then supplies the
    authorization path already bound to that contract.
    """

    authority = load_operational_authority(Path(authority_path))
    mission_id = str(authority.values.get("CURRENT_MISSION") or "").strip()
    if not mission_id or mission_id.upper() == "NONE":
        raise OperationalAuthorityError("NO_ACTIVE_CURRENT_MISSION")

    bundle_reference = authority.values.get("CURRENT_MISSION_EXECUTION_BUNDLE")
    if not isinstance(bundle_reference, str) or not bundle_reference.strip() or bundle_reference.strip().upper() == "NONE":
        raise OperationalAuthorityError("ACTIVE_MISSION_EXECUTION_BUNDLE_REQUIRED")

    root = Path(repository_root).resolve()
    contract_path = _repository_reference(root, bundle_reference.strip(), "ACTIVE_MISSION_EXECUTION_BUNDLE_INVALID")
    try:
        contract = load_mission_contract(contract_path)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise OperationalAuthorityError("ACTIVE_MISSION_EXECUTION_BUNDLE_INVALID") from exc
    if contract.mission_id != mission_id:
        raise OperationalAuthorityError("ACTIVE_MISSION_EXECUTION_BUNDLE_MISSION_MISMATCH")
    authorization_reference = contract.mission_authorization_path
    if not authorization_reference or authorization_reference.upper() == "NONE":
        raise OperationalAuthorityError("ACTIVE_MISSION_AUTHORIZATION_REQUIRED")
    authorization_path = _repository_reference(root, authorization_reference, "ACTIVE_MISSION_AUTHORIZATION_INVALID")
    try:
        authorization = load_mission_authorization(authorization_path)
    except (OSError, UnicodeDecodeError, ValueError, MissionAuthorizationError) as exc:
        raise OperationalAuthorityError("ACTIVE_MISSION_AUTHORIZATION_INVALID") from exc
    if authorization.mission_id != mission_id:
        raise OperationalAuthorityError("ACTIVE_MISSION_AUTHORIZATION_MISSION_MISMATCH")
    return ActiveMissionBundle(
        mission_id=mission_id,
        mission_contract_path=contract_path.relative_to(root).as_posix(),
        mission_authorization_path=authorization_path.relative_to(root).as_posix(),
    )
