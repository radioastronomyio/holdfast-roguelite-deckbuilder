/**
 * Type declarations for the vendored buttons factory.
 * Source of truth: buttons.js (vanilla ES module, untyped).
 */

export type ButtonAccent = "primary" | "success" | "warning" | "danger" | "info" | "magic" | "pink";
export type ButtonVariant = "solid" | "outline" | "ghost" | "pill" | "icon" | "square" | "tab";

export interface ButtonOptions {
  label?: string;
  icon?: string;
  text?: string;
  accent?: ButtonAccent;
  variant?: ButtonVariant;
  ariaLabel?: string;
  disabled?: boolean;
  active?: boolean;
  onClick?: (event: MouseEvent, ctx: { el: HTMLButtonElement }) => void;
}

export interface ButtonControl {
  el: HTMLButtonElement;
  setLabel: (label: string) => void;
  setIcon: (icon: string) => void;
  setAccent: (next: string) => void;
  setVariant: (next: string) => void;
  setDisabled: (disabled: boolean) => void;
  setActive: (active: boolean) => void;
  onClick: (fn: (event: MouseEvent, ctx: { el: HTMLButtonElement }) => void) => void;
}

export function createButton(options?: ButtonOptions): ButtonControl;
