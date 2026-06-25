/**
 * Type declarations for the vendored loading states factory.
 * Source of truth: loading.js (vanilla ES module, untyped).
 */

export interface SpinnerOptions {
  variant?: "ring" | "dot" | "pulse";
  accent?: string;
  size?: "sm" | "md" | "lg";
  label?: string;
}

export interface SpinnerControl {
  el: HTMLElement;
}

export interface LoadingOverlayOptions {
  title?: string;
  message?: string;
  spinner?: "ring" | "dot" | "pulse";
  accent?: string;
  progress?: number;
  showPercent?: boolean;
}

export interface LoadingOverlayControl {
  el: HTMLElement;
  show: () => void;
  hide: () => void;
  isOpen: () => boolean;
  setProgress: (fraction: number) => void;
  setMessage: (text: string) => void;
  setTitle: (text: string) => void;
}

export function createSpinner(options?: SpinnerOptions): SpinnerControl;
export function createLoadingOverlay(options?: LoadingOverlayOptions): LoadingOverlayControl;
