"""Registro persistente y validación de perfiles editoriales."""
import json
from pathlib import Path

from src.core.contract_validation import validate_against_schema
from src.core.version_manifest import compute_checksum


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
        return checksum
