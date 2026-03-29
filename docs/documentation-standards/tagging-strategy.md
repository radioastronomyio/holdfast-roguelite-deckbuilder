<!--
---
title: "Tagging Strategy"
description: "Controlled vocabulary for document classification in holdfast-roguelite-deckbuilder"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-03-29"
version: "2.0"
tags:
  - type: guide
  - domain: documentation
related_documents:
  - "[Interior README Template](interior-readme-template.md)"
  - "[General KB Template](general-kb-template.md)"
  - "[Worklog README Template](worklog-readme-template.md)"
---
-->

# Tagging Strategy

## 1. Purpose

Controlled tag vocabulary for the holdfast-roguelite-deckbuilder repository. Consistent tagging enables human navigation and RAG system retrieval.

---

## 2. Why Controlled Vocabulary

Uncontrolled tagging leads to synonyms fragmenting search, inconsistent granularity, and tag proliferation that reduces signal. A controlled vocabulary defines allowed values upfront, ensuring consistency across contributors and time.

---

## 3. Tag Categories

| Category | Question Answered | Required |
|----------|-------------------|----------|
| `type` | What kind of document is this? | Yes |
| `domain` | What subject area? | Yes |
| `status` | What's the lifecycle state? | Recommended |
| `tech` | What technologies involved? | When applicable |

---

## 4. Domain Tags

| Tag | Use For | Boundary |
|-----|---------|----------|
| `game-design` | GDD, mechanics, systems design, modifier engine, stat model | Design decisions and rules, not implementation |
| `simulation` | Monte Carlo runner, AI heuristics, balance testing, campaign loop | Python simulation code and results |
| `balance` | Tuning values, degenerate signal checks, win rate analysis, reports | Numerical tuning, not mechanical design changes |
| `data-schemas` | Pydantic models, JSON definitions, card/character/region data | Data structures and contracts, not game logic |
| `procedural-gen` | Character/enemy/region/encounter generators, seeded RNG | Generation systems, not the data they produce |
| `frontend` | React game UI, rendering, state management | Browser frontend, not simulation |
| `mods` | Flavor data, word pools, epithet conditions, content layer | Mod-ready content, not core mechanics |
| `research` | GDR outputs, design validation, reference material | Research artifacts, not specs |
| `infrastructure` | Repo structure, tooling, CI, OpenSpec management | Project infrastructure, not game systems |
| `documentation` | Templates, standards, meta-content about the repo itself | Docs about docs |

---

## 5. Type Tags

| Tag | Use For |
|-----|---------|
| `project-root` | Repository root README |
| `directory-readme` | Interior README for any directory |
| `worklog` | Work log entries and milestone documentation |
| `guide` | Step-by-step procedures and how-to documents |
| `reference` | Lookup information: schemas, data dictionaries, stat tables |
| `specification` | Milestone specs, OpenSpec change proposals |
| `report` | Balance analysis, Monte Carlo results, tuning reports |
| `design-doc` | Game design document sections |

---

## 6. Status Tags

| Tag | Description |
|-----|-------------|
| `draft` | In development, not yet complete |
| `active` | Current, maintained, approved |
| `under-review` | Review in progress |
| `deprecated` | Superseded, avoid for new work |
| `archived` | Historical reference only |

---

## 7. Tech Tags

| Tag | Technology |
|-----|-----------|
| `python` | Python simulation code |
| `pydantic` | Data model definitions |
| `pytest` | Test suite |
| `react` | Browser frontend |
| `json` | Shared data definitions |
| `openspec` | Specification management |
| `bash` | Shell scripts |

---

## 8. Implementation

### Standard Frontmatter

```yaml
<!--
---
title: "Document Title"
description: "What this document covers"
author: "VintageDon (https://github.com/vintagedon/)"
date: "YYYY-MM-DD"
version: "1.0"
status: "Active"
tags:
  - type: specification
  - domain: simulation
  - tech: [python, pydantic]
related_documents:
  - "[Related Doc](path/to/doc.md)"
---
-->
```

### Conventions

- Use lowercase, hyphenated values
- Tech tags use canonical names
- One value per line for readability, or array syntax for multi-value
- `related_documents` links use relative paths within the repo

---

## 9. Maintaining the Vocabulary

- This document is the authoritative source for allowed tag values
- Prefer broader tags over proliferating specific ones
- Check for existing coverage before adding new tags
- Backfill existing documents when adding new tags

---

## 10. References

| Resource | Description |
|----------|-------------|
| [Interior README Template](interior-readme-template.md) | Shows tag usage in directory READMEs |
| [General KB Template](general-kb-template.md) | Shows tag usage for standalone docs |
| [Worklog README Template](worklog-readme-template.md) | Shows tag usage for work log entries |
