/* Numerical models used by the interactive explanations. No DOM dependency. */
(() => {
  'use strict';
  const factorial = n => n < 2 ? 1 : n * factorial(n-1);
  const choose = (n,k) => factorial(n)/(factorial(k)*factorial(n-k));
  function coefficients(n,j,d) {
    const q = Math.LN2 / n, scale = 2 ** ((j+.5)/n), c = Array(d+1).fill(0);
    // Expand the Taylor series about t=1/2 into powers of t, so the same
    // Horner datapath can evaluate every row on the residual interval [0,1).
    for (let r = 0; r <= d; ++r)
      for (let p = 0; p <= r; ++p)
        c[p] += scale*q**r/factorial(r)*choose(r,p)*(-.5)**(r-p);
    return c;
  }
  function midpointQuadratic(left, width, x) {
    const midpoint = left + width/2;
    const z = Math.LN2*(x-midpoint);
    // Match exp2 and its first two derivatives at the midpoint. The missing
    // cubic term explains why reducing the interval improves this estimate.
    return 2**midpoint*(1+z+z*z/2);
  }
  function taylorRelativeError(n, degree, t) {
    const z = Math.LN2 / n * (t - .5);
    // Evaluate what the polynomial leaves out. Subtracting two values near
    // one would hide the very small remainder we want the reader to see.
    let term = 1, tail = 0;
    for (let k = 1; k <= 32; ++k) {
      term *= z / k;
      if (k > degree) tail += term;
    }
    return -tail / Math.exp(z);
  }
  function rne(value) {
    const low = Math.floor(value), residual = value-low;
    return low + Number(residual > .5 || (residual === .5 && low%2 === 1));
  }
  function roundShift(raw, shift) {
    if (shift <= 0) return raw << BigInt(-shift);
    const s = BigInt(shift), retained = raw >> s;
    const dropped = raw - (retained << s), half = 1n << (s-1n);
    return retained + BigInt(dropped > half || (dropped === half && (retained & 1n) === 1n));
  }
  function multiplyAdd(a,t,b,fraction) {
    const pf = a.fraction + t.fraction, common = Math.max(pf,b.fraction);
    const product = a.raw*t.raw;
    const sum = (product << BigInt(common-pf)) + (b.raw << BigInt(common-b.fraction));
    const shift = common-fraction;
    return {raw:roundShift(sum,shift), fraction, product, pf, sum, common, shift};
  }
  const value = word => Number(word.raw)*2**(-word.fraction);
  globalThis.SfuMath = Object.freeze({factorial, coefficients, midpointQuadratic, taylorRelativeError, rne, roundShift, multiplyAdd, value});
})();
