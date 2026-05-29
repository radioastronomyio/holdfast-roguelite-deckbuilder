export interface RngState {
  mt: number[];
  index: number;
  callCount: number;
}

const N = 624;
const M = 397;
const MATRIX_A = 0x9908b0df;
const UPPER_MASK = 0x80000000;
const LOWER_MASK = 0x7fffffff;

function uint32(value: number): number {
  return value >>> 0;
}

export class SeededRng {
  private mt: number[] = new Array<number>(N).fill(0);
  private index = N;
  callCount = 0;

  constructor(seed: number) {
    this.seed(seed);
  }

  private seed(seed: number): void {
    const key = [uint32(Math.abs(Math.trunc(seed)))];
    this.initByArray(key);
    this.callCount = 0;
  }

  private initGenRand(seed: number): void {
    this.mt[0] = uint32(seed);
    for (let i = 1; i < N; i += 1) {
      this.mt[i] = uint32((Math.imul(1812433253, this.mt[i - 1] ^ (this.mt[i - 1] >>> 30)) + i));
    }
    this.index = N;
  }

  private initByArray(initKey: number[]): void {
    this.initGenRand(19650218);
    let i = 1;
    let j = 0;
    let k = Math.max(N, initKey.length);
    for (; k > 0; k -= 1) {
      const x = this.mt[i - 1] ^ (this.mt[i - 1] >>> 30);
      this.mt[i] = uint32((this.mt[i] ^ Math.imul(x, 1664525)) + initKey[j] + j);
      i += 1;
      j += 1;
      if (i >= N) {
        this.mt[0] = this.mt[N - 1];
        i = 1;
      }
      if (j >= initKey.length) j = 0;
    }
    for (k = N - 1; k > 0; k -= 1) {
      const x = this.mt[i - 1] ^ (this.mt[i - 1] >>> 30);
      this.mt[i] = uint32((this.mt[i] ^ Math.imul(x, 1566083941)) - i);
      i += 1;
      if (i >= N) {
        this.mt[0] = this.mt[N - 1];
        i = 1;
      }
    }
    this.mt[0] = 0x80000000;
    this.index = N;
  }

  private twist(): void {
    for (let kk = 0; kk < N - M; kk += 1) {
      const y = (this.mt[kk] & UPPER_MASK) | (this.mt[kk + 1] & LOWER_MASK);
      this.mt[kk] = this.mt[kk + M] ^ (y >>> 1) ^ ((y & 1) ? MATRIX_A : 0);
    }
    for (let kk = N - M; kk < N - 1; kk += 1) {
      const y = (this.mt[kk] & UPPER_MASK) | (this.mt[kk + 1] & LOWER_MASK);
      this.mt[kk] = this.mt[kk + (M - N)] ^ (y >>> 1) ^ ((y & 1) ? MATRIX_A : 0);
    }
    const y = (this.mt[N - 1] & UPPER_MASK) | (this.mt[0] & LOWER_MASK);
    this.mt[N - 1] = this.mt[M - 1] ^ (y >>> 1) ^ ((y & 1) ? MATRIX_A : 0);
    this.index = 0;
  }

  private genrandUint32(): number {
    if (this.index >= N) {
      this.twist();
    }
    let y = this.mt[this.index];
    this.index += 1;
    y ^= y >>> 11;
    y ^= (y << 7) & 0x9d2c5680;
    y ^= (y << 15) & 0xefc60000;
    y ^= y >>> 18;
    return uint32(y);
  }

  random(): number {
    this.callCount += 1;
    const a = this.genrandUint32() >>> 5;
    const b = this.genrandUint32() >>> 6;
    return (a * 67108864 + b) / 9007199254740992;
  }

  getrandbits(k: number): number {
    this.callCount += 1;
    if (k < 0 || k > 32) throw new Error("getrandbits supports 0 <= k <= 32");
    if (k === 0) return 0;
    return this.genrandUint32() >>> (32 - k);
  }

  randBelow(n: number): number {
    this.callCount += 1;
    if (!Number.isSafeInteger(n) || n <= 0) throw new Error(`invalid randBelow bound: ${n}`);
    const k = Math.floor(Math.log2(n)) + 1;
    while (true) {
      const r = this.getrandbitsInternal(k);
      if (r < n) return r;
    }
  }

  private getrandbitsInternal(k: number): number {
    if (k === 0) return 0;
    return this.genrandUint32() >>> (32 - k);
  }

  choice<T>(array: T[]): T {
    this.callCount += 1;
    if (array.length === 0) throw new Error("Cannot choose from an empty array");
    return array[this.randBelowInternal(array.length)];
  }

  private randBelowInternal(n: number): number {
    const k = Math.floor(Math.log2(n)) + 1;
    while (true) {
      const r = this.getrandbitsInternal(k);
      if (r < n) return r;
    }
  }

  shuffle<T>(array: T[]): void {
    this.callCount += 1;
    for (let i = array.length - 1; i > 0; i -= 1) {
      const j = this.randBelowInternal(i + 1);
      [array[i], array[j]] = [array[j], array[i]];
    }
  }

  randint(a: number, b: number): number {
    this.callCount += 1;
    return this.randBelowInternal(b - a + 1) + a;
  }

  sample<T>(population: T[], k: number): T[] {
    this.callCount += 1;
    if (k < 0 || k > population.length) throw new Error("Sample larger than population or negative");
    const result: T[] = [];
    const pool = [...population];
    let n = pool.length;
    for (let i = 0; i < k; i += 1) {
      const j = this.randBelowInternal(n);
      result.push(pool[j]);
      pool[j] = pool[n - 1];
      n -= 1;
    }
    return result;
  }

  getState(): RngState {
    return { mt: [...this.mt], index: this.index, callCount: this.callCount };
  }

  setState(state: RngState): void {
    if (state.mt.length !== N) throw new Error("Invalid MT state length");
    this.mt = [...state.mt].map(uint32);
    this.index = state.index;
    this.callCount = state.callCount;
  }
}
