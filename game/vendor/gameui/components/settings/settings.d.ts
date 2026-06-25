/**
 * Type declarations for the vendored settings controls factory.
 * Source of truth: settings.js (vanilla ES module, untyped).
 */

export type SettingAccent = "primary" | "success" | "warning" | "danger" | "info" | "magic" | "pink";

export interface ToggleOptions {
  label?: string;
  checked?: boolean;
  accent?: SettingAccent;
  ariaLabel?: string;
  onChange?: (on: boolean) => void;
}

export interface SwitchOptions {
  label?: string;
  checked?: boolean;
  accent?: SettingAccent;
  ariaLabel?: string;
  onChange?: (on: boolean) => void;
}

export interface SwitchControl {
  el: HTMLElement;
  isChecked: () => boolean;
  setChecked: (next: boolean) => void;
  toggle: () => void;
  setDisabled?: (disabled: boolean) => void;
  onChange: (fn: (on: boolean) => void) => void;
}

export interface SliderOptions {
  label?: string;
  min?: number;
  max?: number;
  step?: number;
  value?: number;
  suffix?: string;
  accent?: SettingAccent;
  ariaLabel?: string;
  onChange?: (value: number) => void;
}

export interface SliderControl {
  el: HTMLElement;
  input: HTMLInputElement;
  getValue: () => number;
  setValue: (next: number) => void;
  setDisabled: (disabled: boolean) => void;
  onChange: (fn: (value: number) => void) => void;
}

export interface SelectOptionEntry {
  value: string;
  label: string;
}

export interface SelectOptions {
  label?: string;
  options?: string[] | SelectOptionEntry[];
  value?: string;
  accent?: SettingAccent;
  ariaLabel?: string;
  onChange?: (value: string) => void;
}

export interface SelectControl {
  el: HTMLElement;
  select: HTMLSelectElement;
  getValue: () => string;
  setValue: (next: string) => void;
  setDisabled: (disabled: boolean) => void;
  onChange: (fn: (value: string) => void) => void;
}

export function createToggle(options?: ToggleOptions): SwitchControl;
export function createSwitch(options?: SwitchOptions): SwitchControl;
export function createSlider(options?: SliderOptions): SliderControl;
export function createSelect(options?: SelectOptions): SelectControl;
