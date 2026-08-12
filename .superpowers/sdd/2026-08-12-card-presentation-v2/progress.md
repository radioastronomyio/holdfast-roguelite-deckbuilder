# SDD ledger — plan: docs/superpowers/plans/2026-08-12-card-presentation-v2.md

Base: `6fb8a7b`
Branch: `spec/2026-08-10-holdfast-06-card-system-rewrite`
Plan preflight: no binding conflicts found; active Amendment 1 supersedes v1 presentation requirements.
Task 1: fix round 1/5 (3 addressed, 0 open — centered header, corner-anchored stats, regression coverage; commits 0dfaa81..a272697)
Task 1: complete (commits 6fb8a7b..a272697, review clean)
Task 2: fix round 1/5 (2 addressed, 0 open — total presentation map and exact layer lock; commits c7785f8..af7b45c)
Task 2: complete (commits a272697..af7b45c, review clean)
Task 3: fix round 1/5 (3 addressed, 1 open — mode contract, upgrade modifiers, deterministic outputs addressed; stale test coverage remained; commits 988ca79..32a2ab2)
Task 3: fix round 2/5 (2 addressed, 0 open — complete stale-path scan and hermetic derivation test; commits 32a2ab2..8d3540f)
Task 3: complete (commits af7b45c..8d3540f, review clean)
Task 4: complete (commits 8d3540f..be0278f; deferred zero-raster module-comment minor resolved in Task 6 commit e3cbc7c)
Task 5: complete (commits be0278f..c4c3b89, review clean)
Task 6: implementation complete; browser and verification gates green; awaiting independent review (commit e3cbc7c).
Task 6: complete (commit e3cbc7c; independent reviewers requested one consolidated integration fix round).
Final review fix round 1/5: derivation/PNG provenance, executable publisher entry point, manifest-backed vector card-back emblem, exact five-layer assertions, full-height gallery evidence, and documentation/SDD consistency addressed in one bounded repo-only change; controller retains ownership of central worklog/registry/defect/review/archive records.
Process note: Amendment 1 originally targeted one commit per A1 gate. Mandatory independent implementer and whole-branch review exposed integration defects after those gate commits, so the review-fix commits are intentionally preserved as evidence instead of rewriting or squashing local history.
