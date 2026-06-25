/**
 * Type declarations for the vendored toast manager factory.
 * Source of truth: toasts.js (vanilla ES module, untyped).
 */

export type ToastType =
  | "achievement" | "primary" | "success" | "reward" | "save" | "item"
  | "info" | "quest" | "tip" | "warning" | "error" | "danger"
  | "magic" | "level" | "secret" | "system";

export interface ToastOptions {
  type?: ToastType;
  title?: string;
  message?: string;
  kicker?: string;
  icon?: string;
  chips?: string[];
  progress?: number;
  compact?: boolean;
  role?: string;
  duration?: number;
}

export interface ToastRegionOptions {
  position?: "top-right" | "top-left" | "top-center" | "bottom-right" | "bottom-left" | "bottom-center";
  duration?: number;
  maxVisible?: number;
  dedupe?: boolean;
  onEnqueue?: (toast: ToastOptions & { id: string }) => void;
}

export interface ToasterControl {
  el: HTMLElement;
  enqueue: (toast: ToastOptions) => string;
  dismiss: (id: string) => void;
  clear: () => void;
  onEnqueue: (fn: (toast: ToastOptions & { id: string }) => void) => void;
}

export function createToaster(options?: ToastRegionOptions): ToasterControl;
