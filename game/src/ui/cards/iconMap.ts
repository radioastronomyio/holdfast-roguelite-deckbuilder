/** Card-tag to GameUI accent resolution retained from the frozen card contract. */

import type { CardAccent } from "../gameui";

const TAG_ACCENT: Record<string, CardAccent> = {
  attack: "danger",
  defense: "info",
  buff: "success",
  heal: "success",
  magic: "magic",
  control: "warning",
  debuff: "warning",
};

export const DEFAULT_ACCENT: CardAccent = "primary";

const TAG_ACCENT_PRECEDENCE = [
  "attack",
  "magic",
  "control",
  "debuff",
  "defense",
  "heal",
  "buff",
];

export function accentForCard(tags: string[]): CardAccent {
  for (const tag of TAG_ACCENT_PRECEDENCE) {
    if (tags.includes(tag)) return TAG_ACCENT[tag];
  }
  return DEFAULT_ACCENT;
}
