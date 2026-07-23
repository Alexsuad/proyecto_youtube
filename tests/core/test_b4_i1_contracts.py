import json
import re
from pathlib import Path
from jsonschema import validate
ROOT = Path(__file__).parents[2]
def read_json(path): return json.loads((ROOT / path).read_text(encoding='utf-8'))
def test_responsibility_registry_schema_and_contracts():
    schema=read_json('schemas/responsibility_registry.json'); registry=read_json('config/responsibility_registry.json'); validate(registry,schema)
    assert [r['role_id'] for r in registry['responsibilities']]==['ORCHESTRATION','RESEARCH_AND_CURATION','NARRATIVE_ARCHITECTURE','WRITING','EDITOR','FINAL_EDITORIAL_AUDITOR']
    assert [r['role_id'] for r in registry['functional_families']]==['CHANNEL_INTELLIGENCE','YOUTUBE_ADAPTATION']
    assert len(registry['legacy_role_mapping'])==11
    editor=next(r for r in registry['responsibilities'] if r['role_id']=='EDITOR'); auditor=next(r for r in registry['responsibilities'] if r['role_id']=='FINAL_EDITORIAL_AUDITOR')
    assert 'script' in editor['write_permissions']; assert 'EditorialEditReport' in editor['outputs']; assert 'script' not in auditor['write_permissions']; assert auditor['outputs']==['FinalEditorialAudit']; assert set(auditor['evidence']) >= {'PASS|WARN|FAIL|BLOCKED','correction route'}
    assert registry['operational_agents']==1 and registry['real_subagents']==0
def test_skill_catalog_is_one_to_one_and_neutral():
    schema=read_json('schemas/skill_catalog.json'); catalog=read_json('config/skill_catalog.json'); validate(catalog,schema)
    expected={p.relative_to(ROOT).as_posix() for p in (ROOT/'.agent/skills').glob('*.md')}; actual={e['path'] for e in catalog['skills']}
    assert len(catalog['skills'])==21; assert actual==expected; assert len(actual)==len(catalog['skills'])
    allowed={'ORCHESTRATION','RESEARCH_AND_CURATION','NARRATIVE_ARCHITECTURE','WRITING','EDITOR','FINAL_EDITORIAL_AUDITOR','CHANNEL_INTELLIGENCE','YOUTUBE_ADAPTATION'}
    assert {e['canonical_owner'] for e in catalog['skills']} <= allowed; assert any(e['classification']=='NEEDS_PRODUCT_DECISION' for e in catalog['skills'])
def test_b4_i1_artifacts_contain_no_legacy_team_or_provider_identifiers():
    paths=['schemas/responsibility_registry.json','config/responsibility_registry.json']; text='\n'.join((ROOT/p).read_text(encoding='utf-8').lower() for p in paths); catalog=read_json('config/skill_catalog.json'); text += '\n' + '\n'.join(' '.join(str(e[k]) for k in ('canonical_owner','classification','target_or_merge_destination','rationale')).lower() for e in catalog['skills'])
    forbidden=[r'team[_ ]?0[1-4]',r'equipo[_ ]?0[1-4]','antigravity','notebooklm','openai','claude','gemini','gpt','codex']; assert not any(re.search(x,text) for x in forbidden)
