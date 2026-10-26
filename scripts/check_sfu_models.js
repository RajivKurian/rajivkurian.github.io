// Numerical checks for the explanatory models; run with the locked Deno.
import '../js/sfu-math.js';
const {coefficients, midpointQuadratic, taylorRelativeError, roundShift, multiplyAdd, value} = globalThis.SfuMath;
function assert(condition, message) { if (!condition) throw Error(message); }
let cases = 0;
// Compare expanded Horner coefficients with the independent centered series.
// The same check also bounds the unquantized error across every supported row.
for(let k=1;k<=7;++k) {
  const n=2**k;
  for(let d=1;d<=3;++d) for(let j=0;j<n;++j) {
    const c=coefficients(n,j,d), q=Math.LN2/n;
    for(let i=0;i<=16;++i) {
      const t=i/16;
      let horner=c[d];for(let p=d-1;p>=0;--p) horner=horner*t+c[p];
      let sum=1,term=1;for(let r=1;r<=d;++r) { term*=q*(t-.5)/r;sum+=term; }
      const centered=2**((j+.5)/n)*sum;
      assert(Math.abs(horner-centered)<2e-15,'Taylor expansion mismatch');
      const truth=2**((j+t)/n), bound=Math.exp(q)*(q/2)**(d+1)/globalThis.SfuMath.factorial(d+1);
      assert(Math.abs((horner-truth)/truth)<=bound+2e-15,'Taylor bound violated');
      assert(Math.abs(taylorRelativeError(n,d,t)-(horner-truth)/truth)<2e-15,'Stable remainder disagrees with direct polynomial');
      ++cases;
    }
  }
}
// All midpoint cases must choose an even destination integer. Rounding a
// positive integer between two midpoints must choose the closer neighbor.
for(let s=1;s<=12;++s) for(let q=0;q<64;++q) {
  const half=1n<<BigInt(s-1), base=BigInt(q)<<BigInt(s);
  assert(roundShift(base+half,s)===BigInt(q+(q%2)),'Midpoint parity');
  assert(roundShift(base+half-1n,s)===BigInt(q),'Below midpoint');
  if(s>1) assert(roundShift(base+half+1n,s)===BigInt(q+1),'Above midpoint');
}
// Independent small-integer reference: nearest integer, parity tie break.
// Vary binary points so product and addend must be aligned in both directions.
for(let af=0;af<=5;++af) for(let bf=0;bf<=7;++bf) for(let f=0;f<=6;++f)
  for(let a=0;a<16;++a) for(let b=0;b<8;++b) {
    const t=11, tf=4;
    const exact=(a*2**-af*t*2**-tf+b*2**-bf)*2**f;
    const lower=Math.floor(exact), fraction=exact-lower;
    const rounded=lower+Number(fraction>.5 || (fraction===.5 && lower%2===1));
    const out=multiplyAdd({raw:BigInt(a),fraction:af},{raw:BigInt(t),fraction:tf},{raw:BigInt(b),fraction:bf},f);
    assert(out.raw===BigInt(rounded),'Fused alignment and rounding mismatch');
    assert(value(out)===rounded*2**-f,'Fixed-point scale mismatch');
    ++cases;
  }
console.log(`Checked ${cases} Taylor and fixed-point cases, plus midpoint parity cases.`);

// A shorter midpoint fit must reduce both endpoint errors. Normalizing by
// a power of two must leave the relative error and curve shape unchanged.
let previous=Infinity;
for(const width of [8,4,2,1,.5,.25]) {
  const endpointError=Math.abs(midpointQuadratic(0,width,0)-1);
  assert(endpointError<previous,'Shorter interval did not improve midpoint fit');
  previous=endpointError;
  for(const left of [-16,-8,-3,0]) for(const f of [0,.25,.5,.75,1]) {
    const x=left+width*f;
    assert(Math.abs(midpointQuadratic(left,width,x)/2**left-midpointQuadratic(0,width,width*f))<1e-12,'Power-of-two normalization changed the fit');
  }
  const midpoint=width/2;
  assert(midpointQuadratic(0,width,midpoint)===2**midpoint,'Midpoint value mismatch');
}
console.log('Checked range-reduction scaling, midpoint matches and shrinking-interval errors.');

// The guided comparisons rely on the remainder's sign and on cancellation of
// the omitted cubic term, not just a decrease in a summary error bound.
for (const n of [16,32]) for (let i=0;i<=256;++i) {
  const t=i/256, z=Math.LN2/n*(t-.5);
  const quadratic=taylorRelativeError(n,2,t), cubic=taylorRelativeError(n,3,t);
  assert(cubic<=0,'Centered cubic should underestimate exp');
  assert(t===.5 || Math.sign(quadratic)===Math.sign(.5-t),'Quadratic error sign');
  assert(Math.abs(quadratic+z**3/(6*Math.exp(z))-cubic)<1e-21,'Cubic correction identity');
}
for (const [degree,low,high] of [[2,7.5,8.5],[3,15,17]]) {
  const ratio=taylorRelativeError(16,degree,0)/taylorRelativeError(32,degree,0);
  assert(ratio>low && ratio<high,'Row doubling error ratio');
}
const first=multiplyAdd({raw:1n,fraction:3},{raw:3n,fraction:2},{raw:1n,fraction:1},4);
const second=multiplyAdd(first,{raw:3n,fraction:2},{raw:1n,fraction:0},8);
assert(first.raw===10n && second.raw===376n,'Worked Horner rounding example');
assert(value(second)-185/128===3/128,'Propagated first-stage rounding error');
console.log('Checked guided row/degree comparisons, cubic cancellation and worked rounding example.');

// Check the integer values and scales printed in Part 2's worked diagram.
const costExample=multiplyAdd({raw:3n,fraction:5},{raw:3n,fraction:2},{raw:5n,fraction:4},4);
assert(costExample.product===9n && costExample.pf===7,'Worked product');
assert(costExample.sum===49n && costExample.common===7,'Worked aligned sum');
assert(costExample.raw===6n && value(costExample)===.375,'Worked rounded register');
assert(value(costExample)-49/128===-1/128,'Worked rounding error');
console.log('Checked Part 2 multiply-add diagram values and scales.');
