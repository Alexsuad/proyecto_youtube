"""Registro persistente y validación de perfiles editoriales."""
import json
from pathlib import Path
from src.core.contract_validation import validate_against_schema
from src.core.version_manifest import compute_checksum

class EditorialProfileRegistry:
    def __init__(self, path: Path):
        self.path = Path(path); self.data = json.loads(self.path.read_text()) if self.path.exists() else {"profiles": {}, "dependencies": {}}
    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True); self.path.write_text(json.dumps(self.data, sort_keys=True, indent=2)+"\n")
    def register(self, profile: dict) -> str:
        errors = validate_against_schema(profile, "editorial_profile")
        if errors: raise ValueError("Perfil inválido: " + "; ".join(errors))
        checksum = compute_checksum(profile); key = f"{profile['profile_id']}@{profile['version']}"
        prior = self.data["profiles"].get(key)
        if prior and prior["checksum"] != checksum: raise ValueError("Sobrescritura silenciosa rechazada")
        self.data["profiles"][key] = {"checksum": checksum, "profile": profile}; self.save(); return checksum
    def add_dependency(self, profile_key: str, artifact_id: str):
        self.data["dependencies"].setdefault(profile_key, [])
        if artifact_id not in self.data["dependencies"][profile_key]: self.data["dependencies"][profile_key].append(artifact_id)
        self.save()
    def dependencies_for(self, profile_key: str): return list(self.data["dependencies"].get(profile_key, []))
    @staticmethod
    def verify_activation(profile: dict, approval: dict | None, technical: dict | None) -> str:
        checksum = compute_checksum(profile)
        if not approval or validate_against_schema(approval, "editorial_profile_approval"):
            raise ValueError("Aprobación funcional inválida")
        if approval.get("decision") != "APPROVE" or approval.get("profile_id") != profile.get("profile_id") or approval.get("profile_version") != profile.get("version") or approval.get("profile_checksum") != checksum:
            raise ValueError("Aprobación funcional no coincide con el perfil")
        if not technical or validate_against_schema(technical, "gate_result"):
            raise ValueError("Validación técnica inválida")
        evidence = technical.get("evidence", {})
        if technical.get("gate_id") != "B3_TECHNICAL_PROFILE_VALIDATION" or technical.get("artifact_id") != profile.get("profile_id") or technical.get("artifact_version") != profile.get("version") or technical.get("status") != "PASS" or technical.get("exit_code") != 0 or evidence.get("profile_checksum") != checksum:
            raise ValueError("Validación técnica no coincide con el perfil")
        return checksum
