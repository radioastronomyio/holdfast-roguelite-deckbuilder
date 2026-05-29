import { pyFloorDiv } from "./math";
import { Operation, SPEED_MIN_FLOOR, SPEED_PCT_CAP, STAT_SCALE, Stacking, Stat, type Modifier } from "./types";

export function applyStacking(modifiers: Modifier[]): Modifier[] {
  const groups = new Map<string, Modifier[]>();
  for (const modifier of modifiers) {
    const key = `${modifier.stat}\u0000${modifier.operation}`;
    const group = groups.get(key);
    if (group) {
      group.push(modifier);
    } else {
      groups.set(key, [modifier]);
    }
  }

  const result: Modifier[] = [];
  for (const group of groups.values()) {
    const stacking = group[group.length - 1]?.stacking;
    if (stacking === Stacking.stack) {
      result.push(...group);
    } else if (stacking === Stacking.replace) {
      result.push(group[group.length - 1]);
    } else if (stacking === Stacking.max) {
      result.push(group.reduce((best, current) => current.value > best.value ? current : best));
    }
  }
  return result;
}

export function calculateStat(base: number, modifiers: Modifier[], stat: Stat = Stat.HP): number {
  const statMods = applyStacking(modifiers.filter((modifier) => modifier.stat === stat));
  let flatSum = 0;
  let pctSum = 0;

  for (const modifier of statMods) {
    if (modifier.operation === Operation.FLAT_ADD) flatSum += modifier.value;
    if (modifier.operation === Operation.FLAT_SUB) flatSum -= modifier.value;
    if (modifier.operation === Operation.PCT_ADD) pctSum += modifier.value;
    if (modifier.operation === Operation.PCT_SUB) pctSum -= modifier.value;
  }

  if (stat === Stat.Speed && pctSum > SPEED_PCT_CAP) {
    pctSum = SPEED_PCT_CAP;
  }

  let result = pyFloorDiv((base + flatSum) * (100 + pctSum), 100);
  for (const modifier of statMods) {
    if (modifier.operation === Operation.MULTIPLY) {
      result = pyFloorDiv(result * modifier.value, STAT_SCALE);
    }
  }

  if (stat !== Stat.HP) {
    result = Math.max(0, result);
  }
  if (stat === Stat.Speed) {
    result = Math.max(result, SPEED_MIN_FLOOR * STAT_SCALE);
  }
  return result;
}
