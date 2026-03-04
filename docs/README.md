<!--
---
title: "Documentation"
description: "Game design documentation and research references for Holdfast"
author: "CrainBramp"
date: "2026-03-03"
version: "1.1"
status: "Active"
tags:
  - type: directory-readme
  - domain: [documentation, game-design]
---
-->

# Documentation

Game design specifications and research references for Holdfast. The GDD is the source of truth for all mechanics, systems, and architecture decisions.

---

## 1. Contents

```
docs/
├── README.md                       # This file
├── game-design-document.md         # Complete GDD — the source of truth
└── research/                       # Reference material from design validation
    └── rouguelite-deckbuilder-research-01.pdf
```

---

## 2. Key Documents

| Document | Purpose | Status |
|----------|---------|--------|
| [game-design-document.md](game-design-document.md) | Complete game design spec — mechanics, systems, architecture, pitfalls | ✅ v1.0 Complete |
| [research/](research/README.md) | Gemini Deep Research output — code samples, card examples, simulation framework | Reference material |

---

## 3. Related

| Document | Relationship |
|----------|--------------|
| [Repository Root](../README.md) | Parent directory |
| [data/](../data/README.md) | JSON definitions derived from the GDD |
| [simulation/](../simulation/README.md) | Implements balance methodology from the GDD |
| [game/](../game/README.md) | Implements UI/architecture from the GDD |
