export function pyFloorDiv(a: number, b: number): number {
  return Math.floor(a / b);
}

export function assertSafeInteger(value: number, label = "value"): void {
  if (!Number.isSafeInteger(value)) {
    throw new Error(`${label} is not a safe integer: ${value}`);
  }
}
