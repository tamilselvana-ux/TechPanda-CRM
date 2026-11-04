import fs from 'node:fs';
import path from 'node:path';

const htmlPath = 'docs/project-docs/DigiPandaCRM_Documentation_v1.0.html';
const html = fs.readFileSync(htmlPath, 'utf8');

// Let's inspect the TOC entries in the HTML
const matches = [...html.matchAll(/<li class="l(\d)"><a href="#([^"]+)"><span class="tn">([^<]+)<\/span><span class="tt">([^<]+)<\/span>/g)];
console.log(`Found ${matches.length} TOC entries:`);
for (const m of matches.slice(0, 20)) {
  console.log(`- Level ${m[1]}: ${m[3]} | ${m[4]} (#${m[2]})`);
}
