/**
 * Holdfast card renderer — composition over the GameUI `createCard` primitive.
 *
 * `createHoldfastCard(card, opts)` turns a `Card` into a finished deckbuilder
 * card: the card name as the title, an energy-cost badge in the header (via the
 * createCard tag slot), one effect row per modifier (icon + operation-aware
 * signed value + target), an upgrade-tier gem, a shine overlay for upgraded
 * cards, and an inspect affordance that opens a detail modal.
 *
 * Composition, not forking: the factory calls `createCard` for the frame and
 * selection/disabled state, then adds Holdfast-specific children to the slots
 * the primitive exposes. It never edits the vendored primitive. Selectable /
 * disabled / onSelect pass straight through so combat (spec 03) can drive hand
 * selection and energy gating later without touching this component.
 *
 * Card JSON effect values are at display scale (Arcane Strike shows 15, not
 * 15000). They are rendered as written; never divided by STAT_SCALE here.
 *
 * @module ui/cards/holdfastCard
 */

import { Operation, Stat, Target } from "../../sim/types";
import type { Card, Modifier, UpgradeTree } from "../../sim/types";
import { createCard, createModal } from "../gameui";
import type { CardAccent, ModalAccent, ModalControl } from "../gameui";
import { createCardArt, createCardSymbol } from "./cardArt";
import { createCostBadge, createUpgradeGem } from "./cardBadges";
import { resolveCardVisual, resolveEffectSymbol } from "./cardMap";
import type { CreateHoldfastCard } from "./contract";
import { accentForCard } from "./iconMap";
import "./card.css";
import "./cards.css";

export type { HoldfastCardControl, HoldfastCardOptions } from "./contract";

/** Target enum → short label for effect rows. */
const TARGET_LABEL: Record<Target, string> = {
  [Target.SELF]: "Self",
  [Target.ALLY_SINGLE]: "Ally",
  [Target.ALLY_ALL]: "Allies",
  [Target.ENEMY_SINGLE]: "Enemy",
  [Target.ENEMY_ALL]: "All Enemies",
  [Target.GLOBAL]: "Global",
};

/**
 * Format a modifier's value with an operation-aware sign. FLAT and PCT
 * operations render with a leading +/−; MULTIPLY renders as a multiplier.
 * Values are at display scale and rendered as written.
 */
export function formatEffectValue(modifier: Modifier): string {
  switch (modifier.operation) {
    case Operation.FLAT_ADD:
      return `+${modifier.value}`;
    case Operation.FLAT_SUB:
      return `-${modifier.value}`;
    case Operation.PCT_ADD:
      return `+${modifier.value}%`;
    case Operation.PCT_SUB:
      return `-${modifier.value}%`;
    case Operation.MULTIPLY:
      return `x${modifier.value}`;
    default:
      return String(modifier.value);
  }
}

/** Duration → human label. 0 = instant (omitted), <0 = permanent, else N turns. */
function formatDuration(duration: number): string {
  if (duration > 0) return `${duration} turn${duration === 1 ? "" : "s"}`;
  if (duration < 0) return "permanent";
  return "";
}

/**
 * Create a Holdfast deckbuilder card from a `Card` definition.
 */
export const createHoldfastCard: CreateHoldfastCard = (card, opts = {}) => {
  const accent = accentForCard(card.tags);
  const rare = !!opts.rare;
  const upgraded = card.upgrade_tier > 0;

  const rules = document.createElement("div");
  rules.className = "hf-card__rules hf-card__effects";
  for (const effect of card.effects) {
    rules.appendChild(buildEffectRow(effect));
  }

  const body = buildFrameBody(card, rules);
  const stats = deriveFooterStats(card);
  const footer = document.createElement("div");
  footer.className = "hf-card__footer";
  footer.appendChild(buildStatSlot("Attack", stats.attack, "hf-card__attack"));

  const tools = document.createElement("div");
  tools.className = "hf-card__tools";
  tools.appendChild(createUpgradeGem(card.upgrade_tier));
  const inspectBtn = buildInspectButton();
  tools.appendChild(inspectBtn);
  footer.appendChild(tools);
  footer.appendChild(buildStatSlot("Guard", stats.guard, "hf-card__guard"));

  const control = createCard({
    title: card.name,
    tag: { label: String(card.energy_cost), accent },
    accent,
    body,
    footer,
    selectable: opts.selectable,
    selected: opts.selected,
    disabled: opts.disabled,
    onClick: opts.onClick,
    onSelect: opts.onSelect,
  });

  const el = control.el;
  el.classList.add("hf-card");
  el.classList.add(`hf-card--${accent}`);
  el.setAttribute("data-card-id", card.id);
  el.setAttribute("data-upgrade-tier", String(card.upgrade_tier));
  const costSlot = el.querySelector<HTMLElement>(".gui-card__tag");
  costSlot?.classList.add("hf-card__cost");
  costSlot?.replaceChildren(createCostBadge(card.energy_cost));
  if (upgraded) el.classList.add("hf-card--upgraded");
  if (rare) el.classList.add("hf-card--rare");
  if (upgraded) el.classList.add("hf-card--shine");

  // Inspect must never toggle selection: it is a stop-propagation action that
  // opens the detail modal independent of the card's selected state.
  let modal: ModalControl | null = null;
  const openInspect = (): void => {
    if (!modal) {
      modal = buildInspectModal(card, accent, opts.upgradeTree);
      document.body.appendChild(modal.el);
    }
    modal.open();
  };
  inspectBtn.addEventListener("click", (event) => {
    event.stopPropagation();
    openInspect();
  });
  inspectBtn.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      event.stopPropagation();
      openInspect();
    }
  });

  return {
    ...control,
    setRare(next: boolean) {
      el.classList.toggle("hf-card--rare", next);
    },
    setEnergyAffordable(affordable: boolean) {
      control.setDisabled(!affordable);
    },
    openInspect,
  };
};

/** Build the art, type, and rules regions that occupy the primitive body slot. */
function buildFrameBody(card: Card, rules: HTMLElement): HTMLElement {
  const body = document.createElement("div");
  body.className = "hf-card__content";

  const art = document.createElement("div");
  art.className = "hf-card__art";
  const visual = resolveCardVisual(card.tags);
  art.appendChild(createCardArt(visual));

  const type = document.createElement("div");
  type.className = "hf-card__type";
  type.textContent = card.tags.map(titleCase).join(" · ");

  body.append(art, type, rules);
  return body;
}

/** Derive compact attack/guard footer values from the universal modifiers. */
function deriveFooterStats(card: Card): { attack: number; guard: number } {
  const attack = Math.max(
    0,
    ...card.effects
      .filter((effect) => effect.stat === Stat.HP && effect.operation === Operation.FLAT_SUB)
      .map((effect) => Math.abs(effect.value)),
  );
  const guard = Math.max(
    0,
    ...card.effects
      .filter(
        (effect) =>
          (effect.stat === Stat.Defense || effect.stat === Stat.HP) &&
          effect.operation === Operation.FLAT_ADD,
      )
      .map((effect) => effect.value),
  );
  return { attack, guard };
}

function buildStatSlot(label: string, value: number, className: string): HTMLElement {
  const slot = document.createElement("div");
  slot.className = `hf-card__stat ${className}`;

  const caption = document.createElement("span");
  caption.className = "hf-card__stat-label";
  caption.textContent = label;

  const amount = document.createElement("strong");
  amount.className = "hf-card__stat-value";
  amount.textContent = String(value);

  slot.append(caption, amount);
  return slot;
}

function titleCase(value: string): string {
  return value.replace(/(^|[_-])([a-z])/g, (_match, _separator: string, letter: string) =>
    letter.toUpperCase(),
  );
}

/** Build one effect row: icon + signed value/stat + target/duration meta. */
function buildEffectRow(modifier: Modifier): HTMLElement {
  const row = document.createElement("div");
  row.className = "hf-card__effect";

  const icon = createCardSymbol(resolveEffectSymbol(modifier), "hf-card__effect-icon");
  row.appendChild(icon);

  const text = document.createElement("div");
  text.className = "hf-card__effect-text";

  const value = document.createElement("span");
  value.className = "hf-card__effect-value";
  value.textContent = `${formatEffectValue(modifier)} ${modifier.stat}`;
  text.appendChild(value);

  const meta = document.createElement("span");
  meta.className = "hf-card__effect-meta";
  const parts = [TARGET_LABEL[modifier.target]];
  const dur = formatDuration(modifier.duration);
  if (dur) parts.push(dur);
  meta.textContent = parts.join(" · ");
  text.appendChild(meta);

  row.appendChild(text);
  return row;
}

/** Build the small inspect button placed in the card footer. */
function buildInspectButton(): HTMLButtonElement {
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "hf-card__inspect";
  btn.setAttribute("aria-label", "Inspect card");
  btn.textContent = "ⓘ";
  return btn;
}

/** Map a card accent to the narrower modal accent palette (info/pink collapse). */
function toModalAccent(accent: CardAccent): ModalAccent {
  if (accent === "info") return "primary";
  if (accent === "pink") return "magic";
  return accent;
}

/**
 * Build the inspect detail modal: a full breakdown of every modifier, the
 * card's type tags, and the upgrade paths from upgrade-trees.json (if any).
 */
function buildInspectModal(card: Card, accent: CardAccent, upgradeTree?: UpgradeTree): ModalControl {
  const body = document.createElement("div");
  body.className = "hf-inspect";

  const tags = document.createElement("p");
  tags.className = "hf-inspect__tags";
  tags.textContent = card.tags.length ? `Tags: ${card.tags.join(", ")}` : "Tags: —";
  body.appendChild(tags);

  for (const effect of card.effects) {
    body.appendChild(buildInspectRow(effect));
  }

  const paths = upgradeTree ? Object.entries(upgradeTree) : [];
  if (paths.length > 0) {
    const heading = document.createElement("h3");
    heading.className = "hf-inspect__heading";
    heading.textContent = "Upgrade Paths";
    body.appendChild(heading);
    for (const [branchId, entry] of paths) {
      body.appendChild(buildUpgradePath(branchId, entry));
    }
  }

  return createModal({
    title: card.name,
    body,
    accent: toModalAccent(accent),
    buttons: [{ label: "Close", closes: true }],
  });
}

/** Build one full-modifier row for the inspect modal. */
function buildInspectRow(modifier: Modifier): HTMLElement {
  const row = document.createElement("div");
  row.className = "hf-inspect__row";

  const top = document.createElement("div");
  top.className = "hf-inspect__row-top";
  const label = document.createElement("span");
  label.className = "hf-inspect__row-label";
  label.textContent = `${modifier.operation} ${modifier.stat}`;
  const value = document.createElement("span");
  value.className = "hf-inspect__row-value";
  value.textContent = formatEffectValue(modifier);
  top.append(label, value);
  row.appendChild(top);

  const detail = document.createElement("div");
  detail.className = "hf-inspect__row-detail";
  const segments = [
    `target: ${TARGET_LABEL[modifier.target]}`,
    `duration: ${modifier.duration < 0 ? "permanent" : modifier.duration}`,
    `stacking: ${modifier.stacking}`,
  ];
  if (modifier.tags.length) segments.push(`tags: ${modifier.tags.join(", ")}`);
  detail.textContent = segments.join(" · ");
  row.appendChild(detail);
  return row;
}

/** Build one upgrade-path entry for the inspect modal. */
function buildUpgradePath(branchId: string, entry: { tier: number; prerequisite: string | null; added_effects: Modifier[] }): HTMLElement {
  const item = document.createElement("div");
  item.className = "hf-inspect__path";

  const head = document.createElement("div");
  head.className = "hf-inspect__path-head";
  const prereq = entry.prerequisite ? ` (requires ${entry.prerequisite})` : "";
  head.textContent = `${branchId} · tier ${entry.tier}${prereq}`;
  item.appendChild(head);

  for (const effect of entry.added_effects) {
    const line = document.createElement("div");
    line.className = "hf-inspect__path-effect";
    line.textContent = `${formatEffectValue(effect)} ${effect.stat} · ${TARGET_LABEL[effect.target]}`;
    item.appendChild(line);
  }
  return item;
}
