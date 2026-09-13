"""Registro persistente y validación de perfiles editoriales."""
import json
from pathlib import Path

from src.core.contract_validation import validate_against_schema
from src.core.evidence_freshness import sha256_path
from src.core.path_resolution import REPO_ROOT
from src.core.version_manifest import compute_checksum


def validate_b3_lineage_cross_registry(
    repository_root: Path | str = REPO_ROOT,
    *,
    registry_path: Path | str | None = None,
    corpus_manifest_path: Path | str | None = None,
    active_profile_path: Path | str | None = None,
) -> list[str]:
    """Validate the active B3 source identity across registries and its file."""
    root = Path(repository_root).resolve()
    registry_file = Path(registry_path or root / "config" / "editorial_profile_registry.json")
    corpus_file = Path(corpus_manifest_path or root / "profiles" / "voice" / "corpus_manifest.json")
    active_file = Path(active_profile_path or root / "config" / "active_editorial_profile.json")
    violations: list[str] = []

    def read_json(path: Path, label: str) -> dict | None:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            violations.append(f"{label} no es legible.")
            return None
        if not isinstance(value, dict):
            violations.append(f"{label} debe ser un objeto JSON.")
            return None
        return value

    registry = read_json(registry_file, "registry editorial")
    corpus = read_json(corpus_file, "manifest del corpus")
    active = read_json(active_file, "pointer activo")
    if not registry or not corpus or not active:
        return violations

    profile_id = str(active.get("ACTIVE_PROFILE_ID") or "")
    profile_version = str(active.get("ACTIVE_PROFILE_VERSION") or "")
    active_key = EditorialProfileRegistry.build_key(profile_id, profile_version)
    if registry.get("active_profile_key") != active_key:
        violations.append("El pointer activo no coincide con active_profile_key.")
    entry = registry.get("profiles", {}).get(active_key) if isinstance(registry.get("profiles"), dict) else None
    if not isinstance(entry, dict):
        violations.append("El registry no contiene la entrada del perfil activo.")
        return violations
    if entry.get("active") is not True or entry.get("status") != "ACTIVE":
        violations.append("La entrada del perfil activo no está marcada como ACTIVE.")
    profile = entry.get("profile")
    if not isinstance(profile, dict):
        violations.append("La entrada activa no contiene un perfil válido.")
        return violations
    if (
        entry.get("profile_id") != profile_id
        or entry.get("version") != profile_version
        or profile.get("profile_id") != profile_id
        or profile.get("version") != profile_version
    ):
        violations.append("La identidad/version del perfil activo no está reconciliada.")
    if (
        active.get("profile_checksum") != entry.get("checksum")
        or compute_checksum(profile) != entry.get("checksum")
    ):
        violations.append("El checksum del pointer, registry y perfil activo no está reconciliado.")

    registry_lineage = [
        item for item in profile.get("source_lineage", [])
        if isinstance(item, dict) and item.get("source_id") == "B3-FUNCTIONAL-SPEC-CANONICAL"
    ]
    corpus_lineage = [
        item for item in corpus.get("source_lineage", [])
        if isinstance(item, dict) and item.get("source_id") == "B3-FUNCTIONAL-SPEC-CANONICAL"
    ]
    if len(registry_lineage) != 1:
        violations.append("El registry debe contener una única identidad B3 verificable.")
    if len(corpus_lineage) != 1:
        violations.append("El corpus debe contener una única identidad B3 verificable.")
    if len(registry_lineage) != 1 or len(corpus_lineage) != 1:
        return violations

    registry_source = registry_lineage[0]
    corpus_source = corpus_lineage[0]
    expected_identity = {
        "source_id": "B3-FUNCTIONAL-SPEC-CANONICAL",
        "locator": "docs/specifications/B3_editorial_profile_functional_specification.md",
        "role": "FUNCTIONAL_SPECIFICATION",
    }
    for label, source in (("registry", registry_source), ("corpus", corpus_source)):
        fields = expected_identity
        if label == "corpus":
            fields = {"source_id": expected_identity["source_id"], "locator": expected_identity["locator"]}
        for field, expected in fields.items():
            if source.get(field) != expected:
                violations.append(f"{label} B3 {field} no coincide con la identidad canónica.")
    for field in ("source_id", "locator"):
        if registry_source.get(field) != corpus_source.get(field):
            violations.append(f"registry y corpus tienen {field} B3 incompatibles.")

    locator = expected_identity["locator"]
    source_file = (root / locator).resolve()
    try:
        source_file.relative_to(root)
    except ValueError:
        violations.append("El locator B3 sale del repositorio.")
        return violations
    if not source_file.is_file():
        violations.append("La fuente física B3 está ausente.")
        return violations
    physical_checksum = sha256_path(source_file)
    for label, source in (("registry", registry_source), ("corpus", corpus_source)):
        if str(source.get("checksum") or "").lower() != physical_checksum:
            violations.append(f"El checksum B3 declarado por {label} no coincide con la fuente física.")
    return violations


def validate_profile_lineage(profile: dict) -> list[str]:
    """Return deterministic lineage violations for one profile payload."""
    violations: list[str] = []
    seen: dict[tuple[str, str, str], str] = {}
    for index, item in enumerate(profile.get("source_lineage", []) if isinstance(profile, dict) else []):
        if not isinstance(item, dict):
            violations.append(f"source_lineage[{index}] debe ser un objeto.")
            continue
        identity = tuple(str(item.get(field) or "") for field in ("source_id", "locator", "role"))
        checksum = str(item.get("checksum") or "")
        if not all(identity):
            violations.append(f"source_lineage[{index}] requiere source_id, locator y role.")
            continue
        prior = seen.get(identity)
        if prior is not None and prior != checksum:
            violations.append(
                "source_lineage contiene checksums incompatibles para la misma identidad: "
                + "|".join(identity)
            )
        seen[identity] = checksum
    return violations


def load_active_profile_authority(
    requested_path: Path | None = None,
    *,
    _profile_path_override: Path | None = None,
) -> dict:
    """Load and fully validate the sole runtime active-profile authority."""
    canonical = (REPO_ROOT / "config" / "active_editorial_profile.json").resolve()
    if requested_path is not None and Path(requested_path).resolve() != canonical:
        raise ValueError("El perfil editorial activo solo puede resolverse desde config/active_editorial_profile.json.")
    selected = Path(_profile_path_override).resolve() if _profile_path_override is not None else canonical
    if not selected.is_file():
        raise ValueError("El archivo canónico del perfil editorial activo está ausente o no es legible.")
    try:
        active = json.loads(selected.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("El archivo canónico del perfil editorial activo no contiene JSON legible.") from exc
    active_errors = validate_against_schema(active, "active_editorial_profile")
    if active_errors:
        raise ValueError("Perfil editorial activo inválido: " + "; ".join(active_errors))
    registry_path = selected.parent / "editorial_profile_registry.json"
    if not registry_path.is_file():
        raise ValueError("El registry editorial canónico está ausente o no es legible.")
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("El registry editorial canónico no contiene JSON legible.") from exc
    registry_errors = validate_against_schema(registry, "editorial_profile_registry")
    if registry_errors:
        raise ValueError("Registry editorial inválido: " + "; ".join(registry_errors))
    if selected == canonical:
        cross_registry_errors = validate_b3_lineage_cross_registry()
        if cross_registry_errors:
            raise ValueError("Lineage B3 cross-registry inválido: " + "; ".join(cross_registry_errors))
    profile_id = active["ACTIVE_PROFILE_ID"]
    profile_version = active["ACTIVE_PROFILE_VERSION"]
    profile_checksum = active["profile_checksum"]
    key = EditorialProfileRegistry.build_key(profile_id, profile_version)
    entry = registry["profiles"].get(key)
    if (
        registry.get("active_profile_key") != key
        or not isinstance(entry, dict)
        or entry.get("active") is not True
        or entry.get("status") != "ACTIVE"
        or entry.get("profile_id") != profile_id
        or entry.get("version") != profile_version
        or entry.get("checksum") != profile_checksum
    ):
        raise ValueError("El pointer del perfil activo no coincide con el registry editorial canónico.")
    profile = entry.get("profile")
    profile_errors = validate_against_schema(profile, "editorial_profile")
    if profile_errors:
        raise ValueError("El perfil registrado activo es inválido: " + "; ".join(profile_errors))
    lineage_errors = validate_profile_lineage(profile)
    if lineage_errors:
        raise ValueError("Lineage del perfil registrado activo inválido: " + "; ".join(lineage_errors))
    if compute_checksum(profile) != profile_checksum:
        raise ValueError("El perfil registrado activo no coincide con su checksum canónico.")
    for section in ("functional_approval", "technical_validation"):
        if active[section]["profile_checksum"] != profile_checksum:
            raise ValueError(f"{section} no coincide con el checksum del perfil activo.")
    return active


class EditorialProfileRegistry:
    DEFAULT_DATA = {
        "registry_version": "1.0.0",
        "active_profile_key": None,
        "profiles": {},
        "dependencies": {},
    }

    def __init__(self, path: Path):
        self.path = Path(path)
        if self.path.exists():
            self.data = json.loads(self.path.read_text(encoding="utf-8"))
        else:
            self.data = json.loads(json.dumps(self.DEFAULT_DATA))
        self._normalize()

    def _normalize(self):
        normalized = json.loads(json.dumps(self.DEFAULT_DATA))
        normalized.update(self.data or {})
        normalized.setdefault("profiles", {})
        normalized.setdefault("dependencies", {})
        normalized.setdefault("active_profile_key", None)
        normalized.setdefault("registry_version", "1.0.0")
        self.data = normalized

    @staticmethod
    def build_key(profile_id: str, version: str) -> str:
        return f"{profile_id}@{version}"

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    def register(self, profile: dict, profile_path: str | None = None, compiled_profile_path: str | None = None) -> str:
        errors = validate_against_schema(profile, "editorial_profile")
        if errors:
            raise ValueError("Perfil inválido: " + "; ".join(errors))
        checksum = compute_checksum(profile)
        key = self.build_key(profile["profile_id"], profile["version"])
        prior = self.data["profiles"].get(key)
        if prior and prior["checksum"] != checksum:
            raise ValueError("Sobrescritura silenciosa rechazada")
        entry = {
            "profile_id": profile["profile_id"],
            "version": profile["version"],
            "checksum": checksum,
            "profile_path": profile_path or (prior or {}).get("profile_path", ""),
            "compiled_profile_path": compiled_profile_path or (prior or {}).get("compiled_profile_path", ""),
            "status": (prior or {}).get("status", "REGISTERED"),
            "active": (prior or {}).get("active", False),
            "profile": profile,
        }
        for field in (
            "approval_path",
            "technical_validation_path",
            "reason",
            "supersedes",
            "superseded_by",
            "approval_checksum",
            "technical_validation_checksum",
        ):
            if prior and field in prior:
                entry[field] = prior[field]
        self.data["profiles"][key] = entry
        self.save()
        return checksum

    def add_dependency(self, profile_key: str, artifact_id: str):
        self.data.setdefault("dependencies", {}).setdefault(profile_key, [])
        if artifact_id not in self.data["dependencies"][profile_key]:
            self.data["dependencies"][profile_key].append(artifact_id)
        self.save()

    def dependencies_for(self, profile_key: str):
        return list(self.data.get("dependencies", {}).get(profile_key, []))

    def mark_invalid_approval_chain(
        self,
        profile: dict,
        *,
        reason: str,
        approval_checksum: str,
        technical_validation_checksum: str,
        profile_path: str,
        compiled_profile_path: str,
        approval_path: str,
        technical_validation_path: str,
        superseded_by: str | None = None,
    ) -> str:
        checksum = self.register(profile, profile_path=profile_path, compiled_profile_path=compiled_profile_path)
        key = self.build_key(profile["profile_id"], profile["version"])
        entry = self.data["profiles"][key]
        entry.update(
            {
                "approval_path": approval_path,
                "technical_validation_path": technical_validation_path,
                "approval_checksum": approval_checksum,
                "technical_validation_checksum": technical_validation_checksum,
                "status": "INVALID_APPROVAL_CHAIN",
                "active": False,
                "reason": reason,
            }
        )
        if superseded_by:
            entry["superseded_by"] = superseded_by
        if self.data.get("active_profile_key") == key:
            self.data["active_profile_key"] = None
        self.save()
        return checksum

    def record_activation(
        self,
        profile: dict,
        approval: dict,
        technical: dict,
        *,
        actor: str,
        profile_path: str,
        compiled_profile_path: str,
        approval_path: str,
        technical_validation_path: str,
        supersedes: str | None = None,
    ) -> str:
        checksum = self.verify_activation(profile, approval, technical)
        key = self.build_key(profile["profile_id"], profile["version"])
        self.register(profile, profile_path=profile_path, compiled_profile_path=compiled_profile_path)
        entry = self.data["profiles"][key]
        entry.update(
            {
                "approval_path": approval_path,
                "technical_validation_path": technical_validation_path,
                "approval_checksum": approval.get("profile_checksum"),
                "technical_validation_checksum": technical.get("evidence", {}).get("profile_checksum"),
                "status": "ACTIVE",
                "active": True,
                "profile": profile,
            }
        )
        entry.pop("reason", None)
        if supersedes:
            entry["supersedes"] = supersedes
            prior = self.data["profiles"].get(supersedes)
            if prior:
                prior["active"] = False
                prior.setdefault("superseded_by", key)
        self.data["active_profile_key"] = key
        self.save()
        return checksum

    @staticmethod
    def verify_activation(profile: dict, approval: dict | None, technical: dict | None) -> str:
        checksum = compute_checksum(profile)
        if not approval or validate_against_schema(approval, "editorial_profile_approval"):
            raise ValueError("Aprobación funcional inválida")
        if (
            approval.get("decision") != "APPROVE"
            or approval.get("profile_id") != profile.get("profile_id")
            or approval.get("profile_version") != profile.get("version")
            or approval.get("profile_checksum") != checksum
        ):
            raise ValueError("Aprobación funcional no coincide con el perfil")
        if not technical or validate_against_schema(technical, "gate_result"):
            raise ValueError("Validación técnica inválida")
        evidence = technical.get("evidence", {})
        if (
            technical.get("gate_id") != "B3_TECHNICAL_PROFILE_VALIDATION"
            or technical.get("artifact_id") != profile.get("profile_id")
            or technical.get("artifact_version") != profile.get("version")
            or technical.get("status") != "PASS"
            or technical.get("exit_code") != 0
            or evidence.get("profile_checksum") != checksum
        ):
            raise ValueError("Validación técnica no coincide con el perfil")
        lineage = profile.get("source_lineage", [])
        lineage_by_id = {item.get("source_id"): item for item in lineage if isinstance(item, dict)}
        functional_source = evidence.get("functional_source")
        if functional_source is not None:
            if not isinstance(functional_source, dict):
                raise ValueError("La fuente funcional de la validación técnica no es válida")
            source_id = functional_source.get("source_id")
            expected_source = lineage_by_id.get(source_id)
            if expected_source is None or any(
                functional_source.get(field) != expected_source.get(field)
                for field in ("source_id", "role", "checksum")
            ):
                raise ValueError("La fuente funcional de la validación técnica no coincide con el lineage")
        lineage_sources = evidence.get("lineage_sources")
        if lineage_sources is not None:
            if not isinstance(lineage_sources, list) or len(lineage_sources) != len(set(lineage_sources)):
                raise ValueError("La validación técnica contiene lineage_sources duplicados o inválidos")
            if set(lineage_sources) != set(lineage_by_id):
                raise ValueError("La validación técnica contiene fuentes de lineage inexistentes o incompletas")
        return checksum
