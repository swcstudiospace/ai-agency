#!/usr/bin/env node
/**
 * Generate multi-platform icons for Tauri desktop + PWA + mobile splash placeholders.
 * Pure Node (zlib PNG) — no sharp/canvas required.
 */
import { createHash } from "node:crypto";
import { deflateSync } from "node:zlib";
import { mkdirSync, writeFileSync, copyFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "..");

function crc32(buf) {
  let c = ~0;
  for (let i = 0; i < buf.length; i++) {
    c ^= buf[i];
    for (let k = 0; k < 8; k++) c = c & 1 ? (0xedb88320 ^ (c >>> 1)) : c >>> 1;
  }
  return ~c >>> 0;
}

function chunk(type, data) {
  const len = Buffer.alloc(4);
  len.writeUInt32BE(data.length);
  const typeB = Buffer.from(type);
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(crc32(Buffer.concat([typeB, data])));
  return Buffer.concat([len, typeB, data, crc]);
}

/** Solid + diagonal brand gradient-ish PNG (RGBA). */
function png(size, { r = 88, g = 60, b = 180 } = {}) {
  const rows = [];
  for (let y = 0; y < size; y++) {
    const row = Buffer.alloc(1 + size * 4);
    row[0] = 0;
    for (let x = 0; x < size; x++) {
      const t = (x + y) / (2 * size);
      const rr = Math.min(255, Math.floor(r + t * 60));
      const gg = Math.min(255, Math.floor(g + (1 - t) * 40));
      const bb = Math.min(255, Math.floor(b + t * 80));
      // rounded-ish alpha near edges for maskable
      const edge = Math.min(x, y, size - 1 - x, size - 1 - y);
      const a = edge < size * 0.06 ? Math.floor((edge / (size * 0.06)) * 255) : 255;
      const i = 1 + x * 4;
      row[i] = rr;
      row[i + 1] = gg;
      row[i + 2] = bb;
      row[i + 3] = a;
    }
    rows.push(row);
  }
  const raw = Buffer.concat(rows);
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(size, 0);
  ihdr.writeUInt32BE(size, 4);
  ihdr[8] = 8;
  ihdr[9] = 6;
  const sig = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);
  return Buffer.concat([
    sig,
    chunk("IHDR", ihdr),
    chunk("IDAT", deflateSync(raw, { level: 9 })),
    chunk("IEND", Buffer.alloc(0)),
  ]);
}

function write(path, buf) {
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, buf);
  console.log("wrote", path, buf.length);
}

// Tauri icons
const tauriIcons = join(root, "src-tauri/icons");
write(join(tauriIcons, "32x32.png"), png(32));
write(join(tauriIcons, "128x128.png"), png(128));
write(join(tauriIcons, "128x128@2x.png"), png(256));
write(join(tauriIcons, "icon.png"), png(512));
// placeholder ico/icns (Tauri accepts; ideally replace with real iconutil/png2icons on macOS)
write(join(tauriIcons, "icon.ico"), png(256));
write(join(tauriIcons, "icon.icns"), png(512));

// PWA / web public icons
const pub = join(root, "public/icons");
write(join(pub, "pwa-192.png"), png(192));
write(join(pub, "pwa-512.png"), png(512));
write(join(pub, "pwa-512-maskable.png"), png(512));
write(join(root, "public/apple-touch-icon.png"), png(180));
write(join(root, "public/favicon.png"), png(64));

// simple SVG favicon
write(
  join(root, "public/favicon.svg"),
  Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#8b5cf6"/><stop offset="50%" stop-color="#22d3ee"/><stop offset="100%" stop-color="#f472b6"/>
  </linearGradient></defs>
  <rect width="64" height="64" rx="16" fill="#0b0b12"/>
  <rect x="8" y="8" width="48" height="48" rx="12" fill="url(#g)"/>
  <rect x="16" y="16" width="32" height="32" rx="8" fill="#0b0b12"/>
</svg>`),
);

console.log("icons ok · hash", createHash("sha1").update(png(64)).digest("hex").slice(0, 8));
