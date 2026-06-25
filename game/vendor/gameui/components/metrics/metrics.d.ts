/**
 * Type declarations for the vendored metrics factory.
 * Source of truth: metrics.js (vanilla ES module, untyped).
 */

export interface FpsSparklineOptions {
  accent?: string;
  window?: number;
  width?: number;
  height?: number;
  source?: "raf" | "manual";
}

export interface FpsSparklineControl {
  el: HTMLElement;
  canvas: HTMLCanvasElement;
  start: () => void;
  stop: () => void;
  push: (fps: number) => void;
  draw: () => void;
  getFps: () => number;
  source: string;
}

export interface FrameTimeOptions {
  accent?: string;
  window?: number;
  source?: "raf" | "manual";
}

export interface FrameTimeStats {
  current: number;
  min: number;
  max: number;
}

export interface FrameTimeControl {
  el: HTMLElement;
  start: () => void;
  stop: () => void;
  push: (ms: number) => void;
  getStats: () => FrameTimeStats;
  source: string;
}

export interface StatRowConfig {
  label: string;
  unit?: string;
  spark?: boolean;
  sparkWindow?: number;
  accent?: string;
  initial?: number;
}

export interface StatRowsOptions {
  title?: string;
  rows: StatRowConfig[];
}

export interface StatRowsControl {
  el: HTMLElement;
  set: (label: string, value: number) => void;
  setRow: (label: string, value: number) => void;
  getRow: (label: string) => string | null;
}

export function createFpsSparkline(options?: FpsSparklineOptions): FpsSparklineControl;
export function createFrameTime(options?: FrameTimeOptions): FrameTimeControl;
export function createStatRows(options?: StatRowsOptions): StatRowsControl;
