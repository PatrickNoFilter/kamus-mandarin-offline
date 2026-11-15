// Smoke test index.html inline script with a fake DOM.
const fs = require("fs");
const vm = require("vm");

function makeEl() {
  return {
    textContent: "", innerHTML: "", value: "", dataset: {},
    classList: { toggle() {}, add() {}, remove() {}, contains() { return false; } },
    addEventListener() {}, appendChild() {}, onclick: null,
    querySelectorAll() { return []; },
    closest() { return null; },
  };
}
const els = {};
const sandbox = {
  console,
  localStorage: { _d: {}, getItem(k) { return this._d[k] || null; }, setItem(k, v) { this._d[k] = v; } },
  navigator: {},
  window: { scrollTo() {} },
  document: {
    getElementById(id) { return (els[id] = els[id] || makeEl()); },
    querySelectorAll() { return []; },
    createElement() { return makeEl(); },
    addEventListener() {},
    body: makeEl(),
  },
};
sandbox.window.document = sandbox.document;
vm.createContext(sandbox);
const dataSrc = fs.readFileSync("data/kamus_data.js", "utf8");
const appSrc = fs.readFileSync("/tmp/app_inline.js", "utf8");
vm.runInContext(dataSrc + "\n" + appSrc, sandbox);

// exercise the app's own search (with mode filter + alias)
const ctx = vm.createContext(sandbox);
function call(fn, arg) {
  return vm.runInContext(`${fn}(${JSON.stringify(arg)}, 5)`, sandbox);
}
const checks = [
  ["belajar", "学"], ["xuexi", "学习"], ["学习", "学习"], ["terima kasih", "谢谢"],
  ["mau", "要"], ["dia", "她"], ["air", "水"], ["jeruk", "橙子"],
];
let pass = 0;
for (const [q, want] of checks) {
  const res = call("searchSmart", q);
  const top = res[0] ? res[0][0] : "-";
  const ok = top === want;
  if (ok) pass++;
  console.log(ok ? "OK  " : "MISS", `"${q}" top=${top} want=${want}`);
}
// mode filter: pinyin mode must not return ID-only matches
vm.runInContext("mode='py'", sandbox);
let r = call("search", "belajar");
console.log("mode=py 'belajar' ->", r.length, "results (expect 0)");
vm.runInContext("mode='id'", sandbox);
r = call("search", "xuexi");
console.log("mode=id 'xuexi' ->", r.length, "results (expect 0)");
vm.runInContext("mode='hz'", sandbox);
r = call("search", "学习");
console.log("mode=hz '学习' ->", r.length, "results, top:", r[0] ? r[0][0] : "-");
vm.runInContext("mode='all'", sandbox);
// card HTML + tone coloring
const html = vm.runInContext("cardHTML(KAMUS.filter(x=>x[0]==='学习')[0], 'belajar')", sandbox);
console.log("card has tone spans:", /class="t2"/.test(html), "| has HSK badge:", /HSK 1/.test(html), "| has mark:", /<mark>belajar<\/mark>/.test(html));
// favorites round-trip
vm.runInContext("toggleFav(KAMUS.filter(x=>x[0]==='学习')[0])", sandbox);
console.log("fav stored:", sandbox.localStorage._d["km_fav"]);
console.log(`\n${pass}/${checks.length} app-search top-1 correct`);
