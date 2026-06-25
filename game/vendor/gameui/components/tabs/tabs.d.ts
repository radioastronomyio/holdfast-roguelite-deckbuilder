/**
 * Type declarations for the vendored tabs factory.
 * Source of truth: tabs.js (vanilla ES module, untyped).
 */

export interface TabEntry {
  id: string | number;
  label?: string;
  icon?: string;
  ariaLabel?: string;
  content?: string | Node;
  disabled?: boolean;
}

export interface TabsOptions {
  orientation?: "top" | "left" | "right";
  accent?: string;
  tabs: TabEntry[];
  initial?: string | number;
  onChange?: (id: string) => void;
}

export interface TabsControl {
  el: HTMLElement;
  select: (id: string | number) => void;
  selected: () => string | null;
  getPanel: (id: string | number) => HTMLElement | null;
  onChange: (fn: (id: string) => void) => void;
}

export function createTabs(options?: TabsOptions): TabsControl;
