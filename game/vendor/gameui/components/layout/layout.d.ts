/**
 * Type declarations for the vendored layout factory.
 * Source of truth: layout.js (vanilla ES module, untyped).
 */

export interface ShellOptions {
  side?: "left" | "right";
  sideWidth?: string;
  sideLabel?: string;
  header?: string | Node;
  sideContent?: string | Node;
  mainContent?: string | Node;
}

export interface ShellControl {
  el: HTMLElement;
  header: HTMLElement;
  side: HTMLElement;
  main: HTMLElement;
  setSideWidth: (width: string) => void;
}

export interface DrawerOptions {
  side?: "left" | "right";
  title?: string;
  accent?: string;
  content?: string | Node;
  closable?: boolean;
  onShow?: () => void;
  onHide?: () => void;
}

export interface DrawerControl {
  el: HTMLElement;
  show: (opener?: Node) => void;
  hide: () => void;
  toggle: (opener?: Node) => void;
  isOpen: () => boolean;
  setContent: (content: string | Node) => void;
  onShow: (fn: () => void) => void;
  onHide: (fn: () => void) => void;
}

export function createShell(options?: ShellOptions): ShellControl;
export function createDrawer(options?: DrawerOptions): DrawerControl;
