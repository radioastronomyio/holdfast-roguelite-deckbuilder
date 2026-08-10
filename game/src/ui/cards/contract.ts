/** Frozen public contract for the Holdfast card adapter. */

import type { Card, UpgradeTree } from "../../sim/types";
import type { CardControl } from "../gameui";

export interface HoldfastCardOptions {
  rare?: boolean;
  selectable?: boolean;
  selected?: boolean;
  disabled?: boolean;
  onClick?: (event: MouseEvent, ctx: { el: HTMLElement }) => void;
  onSelect?: (selected: boolean) => void;
  upgradeTree?: UpgradeTree;
}

export type HoldfastCardControl = CardControl & {
  setRare: (rare: boolean) => void;
  setEnergyAffordable: (affordable: boolean) => void;
  openInspect: () => void;
};

export type CreateHoldfastCard = (
  card: Card,
  opts?: HoldfastCardOptions,
) => HoldfastCardControl;
