#!/usr/bin/env python3
"""
Script Name  : capture.py
Description  : Playwright regression harness for the Holdfast full-DOM GameUI
               frontend. Boots the Vite dev server, walks every placeholder
               screen off the real CampaignStepper, captures a dark-fantasy
               baseline screenshot per screen, and asserts zero console errors
               and zero non-origin network requests (the framework is
               self-contained).
Repository   : holdfast-roguelite-deckbuilder
Author       : VintageDon (https://github.com/vintagedon/)
Created      : 2026-06-22

Usage
-----
    python3 game/tests/capture.py            # capture baselines (dev server)
    python3 game/tests/capture.py --check    # regression check against .sha1
    python3 game/tests/capture.py --build    # build + vite preview acceptance gate

The harness starts the Vite dev server itself on an isolated port, so no manual
`npm run dev` is required. The `--build` mode runs `npm run build`, serves
`dist/` via `vite preview`, and asserts the dark-fantasy skin renders from the
build with zero failed asset requests — the proof that `vite build` (not just
dev) serves the skin. Playwright runs under Chromium headless only.

Walk model
----------
The router marks the active screen with a `data-screen` attribute on the shell
main viewport, and every non-terminal screen carries a `gui-btn[data-advance]`
that drives the real CampaignStepper and re-routes to the phase it returns. The
harness clicks that button, detects the screen transition, and captures the
first occurrence of each screen until the terminal game-over screen is reached.

Step structure
--------------
SCREENS is the ordered list of (step, filename) pairs. Spec 02 (card renderer)
and beyond extend the router/screen graph; new screens append here and gain
their driver in the walk loop. VERIFY maps each step to a GameUI selector the
harness asserts is present in the DOM, proving the framework rendered.
"""

from __future__ import annotations

import hashlib
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

from playwright.sync_api import Page, sync_playwright

# =============================================================================
# Configuration
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parent.parent
BASELINE_DIR = Path(__file__).resolve().parent / "baseline"
CHECK_MODE = "--check" in sys.argv
BUILD_MODE = "--build" in sys.argv

# Vite and the production subdomain both serve the app from their origin root
# (see game/vite.config.ts `base`). Keeping the acceptance harness on the same
# path makes its asset probes exercise the real deployment shape.
BASE_PATH = "/"

# The dark-fantasy preset overrides the --gui-bg token to this value (the token
# default in tokens.css is #020617). Seeing it proves dark-fantasy.css loaded.
DARK_FANTASY_BG = "#0c0a08"

# One representative of each asset family the dark-fantasy skin and card
# renderer depend on, probed explicitly from the preview (see run_build_mode).
# Fonts and card icons are not requested by any production screen during the
# walk (the card gallery is DEV-only; combat lands in spec 04) and @font-face
# files load lazily, so the walk's response stream alone cannot prove they are
# served. Each maps asset path -> acceptable content-type prefix; a masked 404
# (vite preview serves index.html, HTTP 200 text/html, for any missing path)
# fails the expected-type check.
BUILD_ASSET_PROBES: dict[str, str] = {
    "vendor/gameui/themes/dark-fantasy.css": "text/css",
    "vendor/gameui/themes/fonts/Cinzel.ttf": "font/",
    "vendor/gameui/themes/dark-fantasy-assets/panel-bg.webp": "image/",
    "assets/card-art-icons/crossed-swords.svg": "image/svg+xml",
}

# Each placeholder screen, in capture order. (step name, baseline filename).
# New screens (spec 02+) append here.
SCREENS: list[tuple[str, str]] = [
    ("main-menu", "01-main-menu.png"),
    ("campaign-map", "02-campaign-map.png"),
    ("party-select", "03-party-select.png"),
    ("encounter", "04-encounter.png"),
    ("reward", "05-reward.png"),
    ("world", "06-world.png"),
    ("game-over", "07-game-over.png"),
    ("card-gallery", "08-card-gallery.png"),
]
SCREEN_MAP: dict[str, str] = dict(SCREENS)

VIEWPORT = {"width": 1440, "height": 900}
SETTLE_MS = 200              # pause after a screen transition before capture
MAX_ADVANCES = 600          # safety cap on advance-button clicks

# Screens reachable by driving the real stepper from the main menu. The terminal
# game-over screen is captured separately via the dev hook (see captureGameOver)
# because the natural walk only reaches it after a full campaign.
WALK_SCREENS: set[str] = {
    "main-menu", "campaign-map", "party-select", "encounter", "reward", "world",
}

# Each screen must show its framework component. The shell frame is asserted
# globally; VERIFY asserts the per-screen GameUI panel is present.
VERIFY: dict[str, str] = {
    "main-menu": "[data-screen='main-menu'] .gui-panel .gui-btn[data-advance]",
    "campaign-map": "[data-screen='campaign-map'] .gui-panel .gui-btn[data-advance]",
    "party-select": "[data-screen='party-select'] .gui-panel .gui-btn[data-advance]",
    "encounter": "[data-screen='encounter'] .gui-panel .gui-btn[data-advance]",
    "reward": "[data-screen='reward'] .gui-panel .gui-btn[data-advance]",
    "world": "[data-screen='world'] .gui-panel .gui-btn[data-advance]",
    "game-over": "[data-screen='game-over'] .gui-panel .gui-panel__chip",
    # DEV-only showcase: every card renders as a Holdfast card off shared JSON.
    "card-gallery": "[data-screen='card-gallery'] .hf-card",
}


# =============================================================================
# Dev-server lifecycle
# =============================================================================


def free_port() -> int:
    """Return an OS-allocated free TCP port for the dev server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def start_dev_server(port: int) -> subprocess.Popen:
    """Start the Vite dev server (via node; the .bin/vite lacks the exec bit on
    this host) and block until it serves index.html."""
    env = os.environ.copy()
    proc = subprocess.Popen(
        ["node", "node_modules/vite/bin/vite.js", "--port", str(port), "--strictPort"],
        cwd=str(REPO_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )
    import urllib.request

    base = f"http://127.0.0.1:{port}/"
    for _ in range(60):
        if proc.poll() is not None:
            raise RuntimeError("Dev server exited early")
        try:
            with urllib.request.urlopen(base, timeout=1):
                return proc
        except Exception:
            time.sleep(0.25)
    raise RuntimeError("Dev server did not become ready")


# =============================================================================
# Build + preview-server lifecycle (built-output acceptance gate)
# =============================================================================


def run_build() -> None:
    """Run `npm run build` (prebuild -> check:public -> tsc -> vite build) and
    fail loudly with the tool output if it does not succeed. The build is the
    thing under test in --build mode, so a build failure must abort the gate."""
    print("BUILD: npm run build")
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("BUILD FAILED:")
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise RuntimeError("npm run build failed")


def start_preview_server(port: int) -> subprocess.Popen:
    """Start `vite preview` serving dist/ under BASE_PATH and block until the
    app responds. Binds 127.0.0.1 like the dev server."""
    env = os.environ.copy()
    proc = subprocess.Popen(
        ["node", "node_modules/vite/bin/vite.js", "preview", "--port", str(port), "--strictPort"],
        cwd=str(REPO_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )
    import urllib.request

    base = f"http://127.0.0.1:{port}{BASE_PATH}"
    for _ in range(60):
        if proc.poll() is not None:
            raise RuntimeError("Preview server exited early")
        try:
            with urllib.request.urlopen(base, timeout=1):
                return proc
        except Exception:
            time.sleep(0.25)
    raise RuntimeError("Preview server did not become ready")


# =============================================================================
# Capture + verify helpers
# =============================================================================


def current_screen(page: Page) -> str | None:
    """Read the active screen name from the shell main's data-screen attr."""
    el = page.query_selector("[data-screen]")
    if el is None:
        return None
    return el.get_attribute("data-screen")


def current_nonce(page: Page) -> str | None:
    """Read the render nonce — it changes on every router tear-down + mount."""
    el = page.query_selector("[data-render]")
    if el is None:
        return None
    return el.get_attribute("data-render")


def assert_framework(page: Page, step: str, errors: list[str]) -> None:
    """Verify the GameUI component for a screen is present in the DOM."""
    # Global: the shell frame must always be present.
    if page.locator(".gui-shell").count() == 0:
        errors.append(f"framework check failed: {step} missing .gui-shell")
        print(f"    FRAMEWORK-FAIL {step}: .gui-shell")
        return
    selector = VERIFY.get(step)
    if not selector:
        return
    if page.locator(selector).count() == 0:
        errors.append(f"framework check failed: {step} missing {selector}")
        print(f"    FRAMEWORK-FAIL {step}: {selector}")


def assert_dark_fantasy_skin(page: Page, errors: list[str]) -> None:
    """Prove the dark-fantasy preset actually loaded from the build. dark-fantasy
    .css overrides --gui-bg to #0c0a08 (tokens.css default is #020617), so the
    computed token resolves to the dark-fantasy value only when the stylesheet
    loaded. An empty or token-default value means the skin 404'd in the build."""
    bg = page.evaluate(
        "() => getComputedStyle(document.documentElement).getPropertyValue('--gui-bg').trim()"
    )
    if bg.lower() != DARK_FANTASY_BG:
        errors.append(
            f"dark-fantasy skin not applied: --gui-bg={bg!r} (expected {DARK_FANTASY_BG})"
        )
        print(f"    SKIN-FAIL     --gui-bg={bg!r}")
    else:
        print(f"    SKIN-OK       --gui-bg={bg}")


def sha1_of(path: Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def capture(page: Page, filename: str, errors: list[str]) -> None:
    """Screenshot the current viewport to the baseline dir and record its sha1."""
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    shot = BASELINE_DIR / filename
    page.screenshot(path=str(shot), animations="disabled")
    digest = sha1_of(shot)
    sidecar = BASELINE_DIR / f"{filename}.sha1"
    if CHECK_MODE:
        if not sidecar.exists():
            errors.append(f"{filename}: no baseline .sha1")
            print(f"    NO BASELINE  {filename}")
        elif sidecar.read_text().strip() != digest:
            errors.append(f"{filename}: regression")
            print(f"    REGRESSION   {filename}")
        else:
            print(f"    ok           {filename}")
    else:
        sidecar.write_text(f"{digest}\n")
        print(f"    captured     {filename}")


def capture_screen(page: Page, step: str, captured: set[str], errors: list[str]) -> None:
    """Assert + capture a screen if it has not been captured yet."""
    if step in captured:
        return
    page.wait_for_timeout(SETTLE_MS)
    assert_framework(page, step, errors)
    capture(page, SCREEN_MAP[step], errors)
    captured.add(step)


# =============================================================================
# Walk
# =============================================================================


def walk(page: Page, captured: set[str], errors: list[str]) -> None:
    """Boot to the main menu, then click the advance button through the real
    CampaignStepper, capturing the first occurrence of each non-terminal screen.
    Stops once every walk-reachable screen is captured (before the natural walk
    would continue into later regions). The terminal game-over screen is reached
    via the dev hook in captureGameOver."""
    for _ in range(MAX_ADVANCES):
        name = current_screen(page)
        if name is not None and name in SCREEN_MAP:
            capture_screen(page, name, captured, errors)

        # Stop once every non-terminal screen is captured, or the terminal
        # screen appeared, so the walk never continues past the point the
        # world-modifier parity bug would trip a later combat.
        if "game-over" in captured or WALK_SCREENS.issubset(captured):
            return

        # Terminal screen (game-over) has no advance button.
        btn = page.query_selector("[data-advance]")
        if btn is None or not btn.is_visible():
            return

        before = current_nonce(page)
        btn.click()
        # Wait for the router to tear down + mount the next render. The nonce
        # changes every render even when the screen name stays the same
        # (e.g. encounter -> next encounter in the same region).
        page.wait_for_function(
            "(prev) => {"
            "  const el = document.querySelector('[data-render]');"
            "  return el !== null && el.getAttribute('data-render') !== prev;"
            "}",
            arg=before,
            timeout=8000,
        )


def walk_build(page: Page, errors: list[str]) -> set[str]:
    """Built-output walk: drive the real CampaignStepper through the same advance
    buttons as `walk`, asserting the GameUI component renders on each stepper
    screen, but capturing nothing (the visual baselines stay dev-only). The
    terminal game-over and DEV-only card-gallery screens are unreachable from a
    production build (their hooks are DEV-gated), so this covers WALK_SCREENS
    only — which is enough to exercise every asset family (stylesheets, fonts,
    theme webp, card icons) the skin depends on. Returns the captured set."""
    captured: set[str] = set()
    for _ in range(MAX_ADVANCES):
        name = current_screen(page)
        if name is not None and name in WALK_SCREENS and name not in captured:
            page.wait_for_timeout(SETTLE_MS)
            assert_framework(page, name, errors)
            captured.add(name)
            print(f"    screen ok    {name}")

        if WALK_SCREENS.issubset(captured):
            return captured

        btn = page.query_selector("[data-advance]")
        if btn is None or not btn.is_visible():
            return captured

        before = current_nonce(page)
        btn.click()
        page.wait_for_function(
            "(prev) => {"
            "  const el = document.querySelector('[data-render]');"
            "  return el !== null && el.getAttribute('data-render') !== prev;"
            "}",
            arg=before,
            timeout=8000,
        )
    return captured


def capture_game_over(page: Page, captured: set[str], errors: list[str]) -> None:
    """Reach the terminal game-over screen via the dev hook, which drives a
    fresh stepper to defeat through the real CampaignStepper API."""
    if "game-over" in captured:
        return
    page.evaluate("window.__holdfast && window.__holdfast.showGameOver()")
    page.wait_for_selector("[data-screen='game-over']", timeout=8000)
    capture_screen(page, "game-over", captured, errors)


def capture_card_gallery(context, base_url: str, origin: str, captured: set[str], errors: list[str], off_origin: list[str]) -> None:
    """Reach the DEV-only card-gallery route on a FRESH page.

    The gallery is a standalone showcase with no dependency on the campaign
    walk, but capturing it off the walked page is non-deterministic: the walk
    leaves pending timers/promises in the page that perturb the gallery's
    async JSON fetch + render. A fresh page in the same browser context
    isolates the gallery's render from that residue and produces a deterministic
    baseline (the same one a standalone render produces). The dev hook only
    exists in a DEV build, which is what the harness serves.

    The gallery renders asynchronously (it fetches the shared card JSON), so
    after triggering the hook we wait for the Holdfast cards to mount, assert
    the complete JSON-backed SVG composition, then capture the dark-fantasy
    baseline."""
    if "card-gallery" in captured:
        return
    page = context.new_page()
    try:
        page.on(
            "console",
            lambda m: errors.append(f"console.{m.type}: {m.text}") if m.type == "error" else None,
        )
        page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
        page.on("requestfinished", lambda r: off_origin.append(r.url) if is_off_origin(r.url, origin) else None)
        page.on("requestfailed", lambda r: off_origin.append(f"FAILED {r.url}"))

        page.goto(base_url, wait_until="networkidle")
        page.wait_for_selector("[data-screen='main-menu']", timeout=15000)
        page.evaluate("document.fonts.ready")
        page.wait_for_timeout(400)
        page.evaluate(
            "window.__holdfast && window.__holdfast.showCardGallery "
            "&& window.__holdfast.showCardGallery()"
        )
        page.wait_for_selector("[data-screen='card-gallery'] .hf-card", timeout=10000)
        assert_card_gallery(page, errors)
        capture_screen(page, "card-gallery", captured, errors)
    finally:
        page.close()


def assert_card_gallery(page: Page, errors: list[str]) -> None:
    """Assert the complete SVG card catalog and upgraded exemplar contract."""
    state = page.evaluate(
        """() => {
            const catalog = document.querySelector('.hf-gallery__catalog');
            const cards = Array.from(catalog?.querySelectorAll('.hf-card[data-card-id]') || []);
            const ids = cards.map((card) => card.getAttribute('data-card-id'));
            const artUses = cards.map((card) => card.querySelector('.hf-card-art use')?.getAttribute('href') || '');
            const effects = Array.from(catalog?.querySelectorAll('.hf-card__effect') || []);
            const effectUses = effects.map((row) => row.querySelector('use')?.getAttribute('href') || '');
            const firstCard = cards[0];
            const firstSymbol = firstCard?.querySelector('.hf-card-art__symbol');
            return {
                declaredCount: catalog?.getAttribute('data-gallery-card-count') || '',
                cardCount: cards.length,
                uniqueCount: new Set(ids).size,
                missingArtSymbols: artUses.filter((href) => !href.endsWith('.svg#icon')).length,
                effectCount: effects.length,
                missingEffectSymbols: effectUses.filter((href) => !href.endsWith('.svg#icon')).length,
                rasterCount: catalog?.querySelectorAll('img, image').length || 0,
                costThree: catalog?.querySelector("[data-card-id='sweeping_blade_01'] .hf-card-badge--cost text")?.textContent || '',
                catalogShine: catalog?.querySelectorAll('.hf-card--shine').length || 0,
                exemplarShine: document.querySelectorAll('.hf-gallery__pair .hf-card--shine').length,
                exemplarTier: document.querySelector('.hf-gallery__pair .hf-card--shine')?.getAttribute('data-upgrade-tier') || '',
                symbolColor: firstSymbol ? getComputedStyle(firstSymbol).color : '',
                borderColor: firstCard ? getComputedStyle(firstCard).borderTopColor : '',
            };
        }"""
    )
    expected = {
        "declaredCount": "21",
        "cardCount": 21,
        "uniqueCount": 21,
        "missingArtSymbols": 0,
        "missingEffectSymbols": 0,
        "rasterCount": 0,
        "costThree": "3",
        "catalogShine": 0,
        "exemplarShine": 1,
        "exemplarTier": "2",
    }
    for key, value in expected.items():
        if state[key] != value:
            errors.append(f"card-gallery check failed: {key}={state[key]!r} (expected {value!r})")
            print(f"    GALLERY-FAIL  {key}={state[key]!r}")
    if state["effectCount"] <= 0:
        errors.append("card-gallery check failed: no effect rows")
        print("    GALLERY-FAIL  no effect rows")
    if state["symbolColor"] != state["borderColor"]:
        errors.append(
            "card-gallery check failed: SVG symbol does not inherit card accent "
            f"({state['symbolColor']!r} != {state['borderColor']!r})"
        )
        print("    GALLERY-FAIL  SVG symbol/card accent mismatch")
    if not any(error.startswith("card-gallery check failed") for error in errors):
        print("    GALLERY-OK    21 unique JSON cards; SVG symbols, cost, accent, and shine verified")


# =============================================================================
# Network guards
# =============================================================================


def is_off_origin(url: str, origin: str) -> bool:
    """True if a request URL is off-origin (relative to the dev server)."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https", "ws", "wss"):
            return False
        return parsed.netloc != origin
    except Exception:
        return False


# =============================================================================
# Built-output acceptance gate
# =============================================================================


def run_build_mode() -> int:
    """Built-output acceptance gate: build, serve dist/ via vite preview, walk
    the stepper screens, and assert (1) the dark-fantasy skin is applied, (2)
    zero asset requests return 4xx/5xx, (3) zero non-origin requests, and (4)
    zero console/page errors. The dev-mode capture stays separate; this mode
    captures no screenshots — it is a pass/fail gate proving the build, not just
    the dev server, serves the skin."""
    errors: list[str] = []
    failed_responses: list[tuple[int, str]] = []
    off_origin: list[str] = []

    try:
        run_build()
    except RuntimeError as exc:
        print(f"\nFAIL: {exc}")
        return 1

    port = free_port()
    base_url = f"http://127.0.0.1:{port}{BASE_PATH}"
    origin = f"127.0.0.1:{port}"
    server = start_preview_server(port)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(viewport=VIEWPORT)
            page = context.new_page()

            page.on(
                "console",
                lambda m: errors.append(f"console.{m.type}: {m.text}") if m.type == "error" else None,
            )
            page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
            # Asset gate (spec literal): fail on any 4xx/5xx response. Under
            # vite preview a missing asset is masked as HTTP 200 text/html (SPA
            # fallback), so presence is proven separately by the content-type
            # probes below; this listener backstops real 4xx/5xx (e.g. under a
            # strict static server in the later publish step).
            page.on(
                "response",
                lambda r: failed_responses.append((r.status, r.url)) if r.status >= 400 else None,
            )
            page.on("requestfinished", lambda r: off_origin.append(r.url) if is_off_origin(r.url, origin) else None)
            page.on("requestfailed", lambda r: off_origin.append(f"FAILED {r.url}"))

            page.goto(base_url, wait_until="networkidle")
            page.wait_for_selector("[data-screen='main-menu']", timeout=15000)
            page.evaluate("document.fonts.ready")
            page.wait_for_timeout(400)

            assert_dark_fantasy_skin(page, errors)
            captured = walk_build(page, errors)

            # Explicitly fetch a representative of every asset family (skin CSS,
            # font, theme webp, card icon) from the preview and assert each
            # returns its expected media type — not text/html, which is what
            # vite preview's SPA fallback serves for a missing file. These are
            # not otherwise exercised by the walk (no production screen renders
            # cards yet, and fonts load lazily), so this is the deterministic
            # proof that the build serves the full asset set.
            probe_results = page.evaluate(
                """async (spec) => {
                    const out = {};
                    for (const p of Object.keys(spec.probes)) {
                        const r = await fetch(spec.base + p);
                        out[p] = [r.status, r.headers.get('content-type') || ''];
                    }
                    return out;
                }""",
                {"base": base_url, "probes": BUILD_ASSET_PROBES},
            )
            for asset_path, expected_prefix in BUILD_ASSET_PROBES.items():
                status, ctype = probe_results[asset_path]
                ok = status == 200 and expected_prefix in (ctype or "").lower() and "text/html" not in (ctype or "").lower()
                if ok:
                    print(f"    ASSET-OK      {asset_path} -> {status} {ctype}")
                else:
                    errors.append(f"asset probe failed: {asset_path} -> HTTP {status} {ctype} (expected {expected_prefix}*)")
                    print(f"    ASSET-FAIL    {asset_path} -> {status} {ctype}")
            browser.close()

        missing = WALK_SCREENS - captured
        if missing:
            errors.append(f"build walk did not reach: {sorted(missing)}")
            print(f"    MISSING      {sorted(missing)}")
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()

    # Asset acceptance check — the core of the gate.
    if failed_responses:
        print(f"\nASSETS: {len(failed_responses)} failed request(s) — FAIL:")
        for status, url in failed_responses[:20]:
            print(f"  {status}  {url}")
        errors.append("failed asset requests (4xx/5xx)")
    else:
        print("\nASSETS: zero failed requests")

    # Network self-containment check.
    if off_origin:
        print(f"\nNETWORK: {len(off_origin)} non-origin request(s) — FAIL:")
        for url in off_origin[:20]:
            print(f"  {url}")
        errors.append("non-origin network requests")
    else:
        print("\nNETWORK: zero non-origin requests")

    if errors:
        print(f"\nFAIL: {len(errors)} failure(s)")
        for e in errors[:30]:
            print(f"  - {e}")
        return 1

    print("\nbuild gate green")
    return 0


# =============================================================================
# Main
# =============================================================================


def main() -> int:
    if BUILD_MODE:
        return run_build_mode()
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    port = free_port()
    base_url = f"http://127.0.0.1:{port}/"
    origin = f"127.0.0.1:{port}"
    errors: list[str] = []
    off_origin: list[str] = []

    server = start_dev_server(port)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(viewport=VIEWPORT)
            page = context.new_page()

            # Surface console/page errors and non-origin requests.
            page.on(
                "console",
                lambda m: errors.append(f"console.{m.type}: {m.text}") if m.type == "error" else None,
            )
            page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
            page.on("requestfinished", lambda r: off_origin.append(r.url) if is_off_origin(r.url, origin) else None)
            page.on("requestfailed", lambda r: off_origin.append(f"FAILED {r.url}"))

            page.goto(base_url, wait_until="networkidle")
            page.wait_for_selector("[data-screen='main-menu']", timeout=15000)
            # Wait for self-hosted fonts (Cinzel/MedievalSharp) and the webp
            # panel texture to finish loading so the dark-fantasy baseline is
            # deterministic across runs.
            page.evaluate("document.fonts.ready")
            page.wait_for_timeout(400)

            captured: set[str] = set()
            walk(page, captured, errors)
            capture_game_over(page, captured, errors)
            capture_card_gallery(context, base_url, origin, captured, errors, off_origin)

            browser.close()

        # Report any screens that were never reached.
        for step, filename in SCREENS:
            if step not in captured and not CHECK_MODE:
                errors.append(f"screen not captured: {step}")
                print(f"    MISSING      {filename}")
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()

    # Network acceptance check — the self-contained contract.
    if off_origin:
        print(f"\nNETWORK: {len(off_origin)} non-origin request(s) — FAIL:")
        for url in off_origin[:20]:
            print(f"  {url}")
        errors.append("non-origin network requests")
    else:
        print("\nNETWORK: zero non-origin requests")

    # Coverage check.
    expected = {step for step, _ in SCREENS}
    missing = expected - captured
    if missing and not CHECK_MODE:
        print(f"\nCOVERAGE: missing screens: {sorted(missing)}")

    if errors:
        print(f"\nFAIL: {len(errors)} failure(s)")
        for e in errors[:30]:
            print(f"  - {e}")
        return 1

    print("\nall green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
