# GEMINI.md

## Project Overview
**Holdfast** is a browser-based roguelite deckbuilder characterized by a finite campaign and a universal modifier engine. The game is built using a dual-stack architecture:
- **Simulation (Python):** A robust Monte Carlo simulation engine used for balance validation, procedural generation testing, and AI heuristic evaluation.
- **Frontend (React/TypeScript):** A web-based interface for the playable game, designed to consume the same data and logic rules as the simulation.

The project emphasizes spec-driven development, utilizing OpenSpec and AI-assisted workflows. All game mechanics (combat, hazards, upgrades) resolve through a shared 5-stat model (HP, Power, Speed, Defense, Energy).

## Architecture & Tech Stack
- **Data Layer (`data/`):** Shared JSON definitions for cards, characters, regions, and world decks.
- **Simulation Engine (`simulation/`):**
    - **Models:** Pydantic for data validation.
    - **Engine:** Pure-function resolver for combat and encounters.
    - **Generation:** Seeded RNG-based procedural generation for characters and regions.
    - **Agents:** AI heuristics (Aggressive, Defensive, Balanced) for Monte Carlo analysis.
- **Frontend (`game/`):** React with Vite and TypeScript. Porting logic from the Python simulation to TypeScript (`game/src/sim/`).
- **Development Tooling:** OpenSpec for specification management.

## Building and Running

### Simulation (Python)
- **Prerequisites:** Python 3.12+
- **Installation:**
  ```bash
  pip install -r simulation/requirements.txt
  ```
- **Run Tests:**
  ```bash
  pytest simulation/tests/ -v
  ```
- **Run M3 Analysis:**
  ```bash
  python scripts/run_m3_analysis.py
  ```

### Frontend (React)
- **Prerequisites:** Node.js (v18+ recommended)
- **Installation:**
  ```bash
  cd game && npm install
  ```
- **Run Development Server:**
  ```bash
  cd game && npm run dev
  ```
- **Build for Production:**
  ```bash
  cd game && npm run build
  ```
- **Run Vitest:**
  ```bash
  cd game && npm run test
  ```

## Development Conventions

### Coding Standards
- **Integer Arithmetic:** All game math uses integer-only arithmetic with a `STAT_SCALE = 1000` to avoid floating-point issues.
- **Pure Functions:** The `ResolverEngine` must consist of deterministic pure functions with no side effects.
- **Seeded RNG:** All procedural generation must use instances of `random.Random(seed)` (Python) or a deterministic RNG (TypeScript) to ensure reproducibility.
- **Conventional Commits:** Use standard prefixes like `feat:`, `fix:`, `docs:`, `test:`.

### Testing Practices
- **Exhaustive Testing:** The simulation currently has over 370 tests. New features or fixes MUST include corresponding tests.
- **Verification:** Always run `pytest simulation/tests/ -v` before committing any changes to the simulation engine.
- **Frontend Sync:** Ensure that any logic changes in `simulation/` are mirrored in `game/src/sim/` to maintain parity.

### Documentation
- **Source of Truth:** The [Game Design Document (docs/game-design-document.md)](docs/game-design-document.md) is the authoritative source for all mechanics.
- **Milestone Specs:** Execution targets are defined in `spec/` or `openspec/`.
- **Interior READMEs:** Follow the `interior-readme-template.md` for any new directory.

## Critical Constants
- `STAT_SCALE = 1000` (Applied to FLAT card values at load time).
- `SPEED_MIN_FLOOR = 10` (Prevents 0-Speed stun locks).
- `SPEED_PCT_CAP = 75` (Maximum percentage increase for speed).
