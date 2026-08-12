/**
 * Inline the Vite build into one self-contained HTML file.
 *
 * The standalone artifact lives in figures/ and is what gets published, so it
 * must be derivable from the same source the tests run against. Building it by
 * hand once meant the two could silently drift; this makes the figure a build
 * product instead of a copy.
 */
import { readFileSync, writeFileSync, readdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const dist = join(here, "..", "dist");
const out = join(here, "..", "..", "figures", "pmt_observatory_standalone.html");

let html = readFileSync(join(dist, "index.html"), "utf8");

const assets = join(dist, "assets");
for (const name of readdirSync(assets)) {
  const body = readFileSync(join(assets, name), "utf8");
  if (name.endsWith(".js")) {
    // Vite emits <script type="module" crossorigin src="/assets/x.js"></script>.
    const tag = new RegExp(`<script[^>]*src="[^"]*${name}"[^>]*></script>`);
    if (!tag.test(html)) throw new Error(`no script tag found for ${name}`);
    html = html.replace(tag, `<script type="module">\n${body}\n</script>`);
  } else if (name.endsWith(".css")) {
    const tag = new RegExp(`<link[^>]*href="[^"]*${name}"[^>]*>`);
    if (!tag.test(html)) throw new Error(`no link tag found for ${name}`);
    html = html.replace(tag, `<style>\n${body}\n</style>`);
  }
}

if (/src="\/assets|href="\/assets/.test(html)) {
  throw new Error("standalone still references external assets");
}

writeFileSync(out, html);
console.log(`standalone: ${out} (${(html.length / 1024).toFixed(1)} kB)`);
