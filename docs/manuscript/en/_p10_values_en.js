// Phase 10 value accessors. Every number comes from p10_values.json (written by phase10/make_p10_values.py
// from phase10/results/ only).
const V10 = JSON.parse(fs.readFileSync(path.join(EN_DIR, "p10_values.json"), "utf8").replace(/\bNaN\b/g, "null"));
const near = (a, b) => Math.abs(Number(a) - Number(b)) < 1e-9;
const KEY_EXIST = "pooled|W_COUNT_AU", KEY_HCOUNT = "host|W_COUNT_AU";
const KEY_P10 = `${V10.selection.selected.ref}|${V10.selection.selected.method}`;
const RHO0 = V10.selection.selected.rho0;
function d10(key, W, rho, group = "unseen", F = 1000) {
  const r = V10.detection_group_mean_sd.find((x) => x.key === key && x.W === W && near(x.rho, rho) && x.F === F && x.group === group);
  if (!r) throw new Error(`d10 missing ${key} ${W} ${rho} ${group} ${F}`);
  return r;
}
function c10(key, W, F = 1000) {
  const r = V10.benign_cost_compliance.find((x) => x.key === key && String(x.W) === String(W) && x.F === F);
  if (!r) throw new Error(`c10 missing ${key} ${W} ${F}`);
  return r;
}
const cW = (key, W, F = 1000) => { try { return c10(key, W, F); } catch (e) { return c10(key, "all", F); } };
function fam10(key, W, rho, family, F = 1000) {
  const r = V10.detection_family_mean_sd.find((x) => x.key === key && x.W === W && near(x.rho, rho) && x.family === family && x.F === F);
  if (!r) throw new Error(`fam10 missing ${key} ${W} ${rho} ${family}`);
  return r;
}
function dl10(key, W, rho, group = "unseen", F = 1000) {
  const r = V10.delay_group.find((x) => x.key === key && x.W === W && near(x.rho, rho) && x.group === group && x.F === F);
  if (!r) throw new Error(`dl10 missing ${key} ${W} ${rho}`);
  return r;
}
const prim10 = (W, rho) => V10.primary_comparison.find((x) => x.W === W && near(x.rho, rho));
const ex10 = (A, B, W, rho, oracle) => V10.exploratory_comparisons.find((x) => x.A === A && x.B === B && x.W === W && near(x.rho, rho)
  && x.analysis.startsWith(oracle ? "DIAGNOSTIC" : "EXPLORATORY"));
function mf10(key, W, rho, group = "unseen") {
  const r = V10.matched_fe1_summary.find((x) => x.key === key && x.W === W && near(x.rho, rho) && x.group === group);
  if (!r) throw new Error(`mf10 missing ${key} ${W} ${rho}`);
  return r;
}
const val10 = (ref, method, rho0) => V10.validation.find((x) => x.ref === ref && x.method === method && near(x.rho0, rho0));
const het10 = (label, split) => V10.heterogeneity.find((x) => x.label === label && x.split === split);
const ov10 = (prefix) => V10.overhead.find((x) => x.rule.startsWith(prefix));
const ML10 = {
  W_COUNT_AU: "count, p ≤ α+β", W_COUNT_A: "count, p ≤ α", W_FISHER: "Fisher", W_TPM: "truncated product", W_MINP: "min-p (Tippett)",
  W_HC: "Higher Criticism", W_EVID: "LR e-value window", BCUSUM: "Bernoulli CUSUM", EWMA_FLAG: "EWMA (flag)", EWMA_NLP: "EWMA (−log p)",
  E_CUSUM: "e-CUSUM", E_SR: "e-SR", E_CUSUM_MIX: "e-CUSUM, mixture calibrator", E_CUSUM_LEAKY: "leaky e-CUSUM",
  E_SR_ADAPT: "adaptive e-SR", E_CUSUM_TH: "e-CUSUM, theory threshold", E_SR_TH: "e-SR, theory threshold",
  E_SR_ADAPT_TH: "adaptive e-SR, theory threshold",
};
const RL10 = { pooled: "pooled", host: "host-cond." };
const lab10 = (key) => { const [r, m] = key.split("|"); return `${ML10[m]} [${RL10[r]}]`; };
const pcs = (r) => `${pc(r.mean)} ± ${pt(r.std)}`;
const f2 = (v) => nf(v, 2);
const pvh = (p) => (p < 0.001 ? "< 0.001" : nf(p, 3));
