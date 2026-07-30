import { copyFile, stat } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const source = join(
  root,
  "custom_components",
  "document_sender",
  "frontend_src",
  "document-sender-panel.js",
);
const output = join(
  root,
  "custom_components",
  "document_sender",
  "frontend",
  "document-sender-panel.js",
);
const litBundle = join(
  root,
  "custom_components",
  "document_sender",
  "frontend",
  "lit-core.min.js",
);

await stat(litBundle);
await copyFile(source, output);
