/**
 * GameUI factory bridge — typed re-export of the vendored framework factories.
 *
 * This module is the single boundary between Holdfast's TypeScript code and
 * the vendored vanilla-JS framework under vendor/gameui/. Every game module
 * that needs a live framework control imports from here, not from the vendor
 * path directly, so the JS dependency surface stays in one auditable place.
 *
 * Imports are extensionless: TypeScript resolves them to the co-located
 * .d.ts declarations, and Vite resolves them to the .js source at runtime.
 *
 * @module ui/gameui
 */

export { createButton } from "../../vendor/gameui/components/buttons/buttons";
export type { ButtonOptions, ButtonControl, ButtonAccent, ButtonVariant } from "../../vendor/gameui/components/buttons/buttons";
export { createShell, createDrawer } from "../../vendor/gameui/components/layout/layout";
export type { ShellOptions, ShellControl, DrawerOptions, DrawerControl } from "../../vendor/gameui/components/layout/layout";
export { createModal } from "../../vendor/gameui/components/modals/modals";
export type { ModalOptions, ModalControl, ModalButtonConfig, ModalAccent } from "../../vendor/gameui/components/modals/modals";
export { createCard } from "../../vendor/gameui/components/cards/cards";
export type { CardOptions, CardControl, CardTag, CardAccent } from "../../vendor/gameui/components/cards/cards";
export {
  createToggle,
  createSwitch,
  createSlider,
  createSelect,
} from "../../vendor/gameui/components/settings/settings";
export type {
  ToggleOptions,
  SwitchOptions,
  SwitchControl,
  SliderOptions,
  SliderControl,
  SelectOptions,
  SelectControl,
  SelectOptionEntry,
} from "../../vendor/gameui/components/settings/settings";
export { createTabs } from "../../vendor/gameui/components/tabs/tabs";
export type { TabsOptions, TabsControl, TabEntry } from "../../vendor/gameui/components/tabs/tabs";
export { createToaster } from "../../vendor/gameui/components/toasts/toasts";
export type { ToasterControl, ToastRegionOptions, ToastOptions, ToastType } from "../../vendor/gameui/components/toasts/toasts";
export { createSpinner, createLoadingOverlay } from "../../vendor/gameui/components/loading/loading";
export type { SpinnerOptions, SpinnerControl, LoadingOverlayOptions, LoadingOverlayControl } from "../../vendor/gameui/components/loading/loading";
export { createFpsSparkline, createFrameTime, createStatRows } from "../../vendor/gameui/components/metrics/metrics";
export type { FpsSparklineOptions, FpsSparklineControl, FrameTimeOptions, FrameTimeControl, FrameTimeStats, StatRowConfig, StatRowsOptions, StatRowsControl } from "../../vendor/gameui/components/metrics/metrics";
export { createSfxManager } from "../../vendor/gameui/components/sfx/sfx";
export type { SfxManagerOptions, SfxManagerControl, SfxMapping } from "../../vendor/gameui/components/sfx/sfx";
