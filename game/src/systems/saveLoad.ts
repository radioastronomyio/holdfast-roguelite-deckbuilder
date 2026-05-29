import type { GameData } from "../sim/types";
import { CampaignStepper } from "../sim/campaignStepper";

const SAVE_KEY = "holdfast_save";

export function saveCampaign(stepper: CampaignStepper): void {
  localStorage.setItem(SAVE_KEY, JSON.stringify(stepper.toJSON()));
}

export function loadCampaign(gameData: GameData): CampaignStepper | null {
  const raw = localStorage.getItem(SAVE_KEY);
  if (!raw) return null;
  return CampaignStepper.fromJSON(JSON.parse(raw), gameData);
}

export function clearSave(): void {
  localStorage.removeItem(SAVE_KEY);
}

export function exportBugReport(stepper: CampaignStepper): void {
  const blob = new Blob([JSON.stringify(stepper.toJSON(), null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `holdfast-run-${stepper.seed}.json`;
  link.click();
  URL.revokeObjectURL(url);
}
