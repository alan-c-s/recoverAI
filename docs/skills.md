# RecoverAI — Agent Skills Directory ([skills.sh](https://www.skills.sh/) Specification)

## 1. Overview
RecoverAI implements standard Agent Skills conforming to the open [skills.sh](https://www.skills.sh/) specification and Antigravity Agent framework. Skills are self-contained procedural knowledge packages defined by a `SKILL.md` file containing YAML frontmatter (`name`, `description`) and structured execution guidelines.

Location of project skills: `.agents/skills/`

---

## 2. Installed & Custom Agent Skills Catalog

| Skill Name | Location | Description |
| :--- | :--- | :--- |
| `recovery-companion-agent` | `.agents/skills/recovery-companion-agent/SKILL.md` | Trauma-informed recovery conversation protocols, empathy rules, relapse triage, and crisis management guidelines. |
| `voice-processing-skill` | `.agents/skills/voice-processing-skill/SKILL.md` | Web Audio streaming specification, Whisper STT, audio sentiment analysis, and voice biomarker tracking rules. |
| `rag-memory-skill` | `.agents/skills/rag-memory-skill/SKILL.md` | Long-term memory extraction, pgvector embedding generation, similarity search, and context assembly. |
| `caregiver-alert-skill` | `.agents/skills/caregiver-alert-skill/SKILL.md` | Real-time risk scoring classification, caregiver escalation protocols, SMS/Push notification dispatch, and dashboard alerts. |

---

## 3. Usage & Integration

Skills are automatically loaded by AI agents interacting with the RecoverAI workspace. Agents invoke these procedural guidelines when performing tasks related to voice processing, memory storage, risk prediction, and patient conversations.
