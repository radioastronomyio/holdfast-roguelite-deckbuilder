<!--
---
title: "Research References"
description: "Design validation research outputs for Holdfast"
author: "CrainBramp"
date: "2026-03-03"
version: "1.0"
status: "Active"
tags:
  - type: directory-readme
  - domain: [research, game-design]
---
-->

# Research References

Raw research outputs used to validate and refine the Holdfast game design. These are reference material — the [GDD](../game-design-document.md) is the authoritative spec.

---

## 1. Contents

```
research/
├── README.md                                       # This file
└── rouguelite-deckbuilder-research-01.pdf          # GDR output (March 2026)
```

---

## 2. Documents

| Document | Source | Date | Notes |
|----------|--------|------|-------|
| [rouguelite-deckbuilder-research-01.pdf](rouguelite-deckbuilder-research-01.pdf) | Gemini Deep Research (NSB-bounded) | 2026-03 | Universal modifier model, JSON schemas, card examples, upgrade trees, world deck cards, React component architecture, combat pseudocode, pitfall checklist |

---

## 3. How This Was Used

The GDR prompt was written using Negative Space Bounding (NSB) methodology to constrain the research scope. The output was evaluated, gaps identified (missing character draft mechanic, research layering, skip system, party size cap), and the complete GDD was written incorporating both the GDR findings and design decisions made during conversation.

The GDR output should not be treated as spec — it informed the GDD but the GDD supersedes it where they differ.

---

## 4. Related

| Document | Relationship |
|----------|--------------|
| [docs/](../README.md) | Parent directory |
| [Game Design Document](../game-design-document.md) | Authoritative spec that incorporates this research |
