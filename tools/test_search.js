// Test harness v2: scoring-based ranking.
const fs = require("fs");
const src = fs.readFileSync("data/kamus_data.js", "utf8");
eval(src + "\n;globalThis.KAMUS=KAMUS;globalThis.KAMUS_META=KAMUS_META;");

function normQ(q) {
  return q
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[0-9]/g, "")
    .replace(/[^a-z\u4e00-\u9fff]/g, "");
}

function search(qRaw, limit = 8) {
  const q = qRaw.toLowerCase().trim();
  const qn = normQ(qRaw);
  const scored = [];
  for (let i = 0; i < KAMUS.length; i++) {
    const r = KAMUS[i];
    const [simp, trad, py, plain, gloss] = r;
    const hsk = r[6] || 0;
    const gl = gloss.toLowerCase();
    const senses = gl.split(";").map((s) => s.trim());
    const tokens = gl.split(/[^a-z]+/);
    let base = 0;
    let pos = 0;
    if (simp === q || trad === q) base = 1000;
    else if (senses.includes(q)) base = 950;
    else if (qn.length >= 2 && plain === qn) base = 850;
    else if (simp.startsWith(q) || trad.startsWith(q)) base = 500;
    else if (gl.startsWith(q) && (gl.length === q.length || /[^a-z]/.test(gl[q.length]))) base = 400;
    else if (qn.includes(" ") && gl.includes(q)) { base = 350; pos = gl.indexOf(q); }
    else if (qn.length >= 2 && tokens.includes(qn)) { base = 300; pos = gl.indexOf(qn); }
    else if (qn.length >= 2 && plain.startsWith(qn)) base = 250;
    else if (qn.length >= 2 && tokens.some((w) => w.startsWith(qn))) base = 200;
    else if (gl.includes(q) || py.toLowerCase().includes(q) || (qn.length >= 2 && plain.includes(qn))) base = 100;
    else continue;
    const hskBonus = hsk ? 800 - hsk * 100 : 0;
    const shortBonus = simp.length === 1 ? 40 : simp.length === 2 ? 20 : 0;
    const posPenalty = Math.min(50, Math.floor(pos / 10));
    scored.push([base + hskBonus + shortBonus - posPenalty, i]);
  }
  scored.sort((a, b) => b[0] - a[0] || a[1] - b[1]);
  return scored.slice(0, limit).map((s) => KAMUS[s[1]]);
}

const ALIAS = {
  mau: "ingin",
  "nggak": "tidak",
  gak: "tidak",
  "enggak": "tidak",
  gue: "saya",
  gw: "saya",
  lo: "kamu",
  lu: "kamu",
  makasih: "terima kasih",
  udah: "sudah",
  banget: "sangat",
};

function searchWithAlias(qRaw, limit = 8) {
  const q = qRaw.toLowerCase().trim();
  const formal = ALIAS[q];
  let res = search(formal || qRaw, limit);
  if (formal) {
    const seen = new Set(res.map((r) => r[0] + "|" + r[3]));
    for (const r of search(qRaw, limit)) {
      if (!seen.has(r[0] + "|" + r[3])) res.push(r);
      if (res.length >= limit) break;
    }
  }
  return res.slice(0, limit);
}

const cases = [
  ["belajar", "学"], // 学 = belajar (benar); 学习 ada di #2,
  ["xuexi", "学习"],
  ["xuéxí", "学习"],
  ["xue2xi2", "学习"],
  ["学习", "学习"],
  ["jeruk", "橙子"],
  ["ni hao", "你好"],
  ["zhongguo", "中国"],
  ["air", "水"],
  ["teman", "朋友"],
  ["makan", "吃"],
  ["saya", "我"],
  ["uang", "钱"],
  ["rumah", "家"],
  ["cinta", "爱心"], // 爱心 = cinta (nomina); 爱 ada di hasil,
  ["terima kasih", "谢谢"],
  ["dia", "她"],
  ["mau", "要"],
  ["nggak", "不"],
  ["makasih", "谢谢"],
];
let pass = 0;
for (const [q, want] of cases) {
  const t0 = Date.now();
  const res = searchWithAlias(q);
  const top = res[0] ? res[0][0] : "-";
  const ok = top === want ? "OK " : "MISS";
  if (top === want) pass++;
  console.log(`${ok} "${q}" (${Date.now() - t0}ms) top=${top} want=${want} | ${res.slice(0, 3).map((r) => `${r[0]} ${r[2]}`).join(" ; ")}`);
}
console.log(`\n${pass}/${cases.length} top-1 correct`);
