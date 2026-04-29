import fs from 'fs';
import path from 'path';
import https from 'https';
import { fileURLToPath } from 'url';

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const mediaDir = path.join(rootDir, 'public', 'media');
const tsvPath = path.join(rootDir, 'posts.tsv');
const outPath = path.join(rootDir, 'posts.local.tsv');

fs.mkdirSync(mediaDir, { recursive: true });

function download(url, dest) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(dest);

    const req = https.get(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
      },
    }, (res) => {
      if (res.statusCode === 301 || res.statusCode === 302) {
        file.destroy();
        try { fs.unlinkSync(dest); } catch {}
        download(res.headers.location, dest).then(resolve).catch(reject);
        return;
      }
      if (res.statusCode !== 200) {
        file.destroy();
        try { fs.unlinkSync(dest); } catch {}
        reject(new Error(`HTTP ${res.statusCode}`));
        return;
      }
      res.pipe(file);
      file.on('finish', () => file.close(() => resolve()));
      file.on('error', reject);
    });

    req.on('error', (err) => {
      file.destroy();
      try { fs.unlinkSync(dest); } catch {}
      reject(err);
    });
  });
}

const lines = fs.readFileSync(tsvPath, 'utf8').split('\n');
const [header, ...rest] = lines;
const newLines = [header];

for (const line of rest) {
  if (!line.trim()) { newLines.push(line); continue; }

  const cols = line.split('\t');
  const id = cols[0]?.trim();
  const mediaUrl = cols[3]?.trim();

  if (!id || !mediaUrl?.startsWith('http')) { newLines.push(line); continue; }

  const filename = `${id}.jpg`;
  const dest = path.join(mediaDir, filename);

  process.stdout.write(`[${id.padStart(2)}] `);
  try {
    await download(mediaUrl, dest);
    const kb = Math.round(fs.statSync(dest).size / 1024);
    console.log(`✓  ${filename}  (${kb} KB)`);
    cols[3] = `public/media/${filename}`;
  } catch (e) {
    console.log(`✗  ${e.message}`);
  }

  newLines.push(cols.join('\t'));
}

fs.writeFileSync(outPath, newLines.join('\n'));
console.log(`\nWrote ${outPath}`);
