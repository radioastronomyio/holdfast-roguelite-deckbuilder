/**
 * Type declarations for the vendored SFX manager factory.
 * Source of truth: sfx.js (vanilla ES module, untyped).
 */

export interface SfxMapping {
  [event: string]: string[];
}

export interface SfxManagerOptions {
  audioBasePath?: string;
  mapping?: SfxMapping;
  muted?: boolean;
  volume?: number;
  storageKey?: string;
}

export interface SfxManagerControl {
  play: (name: string) => void;
  setMuted: (muted: boolean) => void;
  isMuted: () => boolean;
  setVolume: (volume: number) => void;
  setMapping: (event: string, files: string[]) => void;
  preload: (names?: string[]) => void;
}

export function createSfxManager(options?: SfxManagerOptions): SfxManagerControl;
