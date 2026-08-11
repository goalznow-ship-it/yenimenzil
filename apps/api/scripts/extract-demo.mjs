/**
 * Extract the frontend demo listings into a plain JSON file that the Python
 * seed script (scripts/seed.py) can consume.
 *
 * The demo module (apps/web/src/data/listings.ts) is TypeScript with a single
 * runtime import (./images); we transpile it with the typescript package that
 * ships inside apps/web/node_modules and evaluate it in a Node VM with that
 * import mocked, then dump `demoListings` as JSON.
 *
 * Usage: node scripts/extract-demo.mjs   (from apps/api)
 */
import { createRequire } from "node:module";
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import vm from "node:vm";

const __dirname = dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);

const API_DIR = resolve(__dirname, "..");
const WEB_DIR = resolve(API_DIR, "..", "web");
const SOURCE = join(WEB_DIR, "src", "data", "listings.ts");
const OUTPUT = join(__dirname, "demo_listings.json");

// apps/api has no node_modules; load typescript from the web workspace.
const ts = require(resolve(WEB_DIR, "node_modules", "typescript"));

const source = readFileSync(SOURCE, "utf8");
const js = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2022,
    esModuleInterop: true,
  },
}).outputText;

// Mock the runtime imports of the demo module. images.ts is self-contained
// TypeScript; transpile and evaluate it inside the same sandbox.
const imagesSource = readFileSync(join(WEB_DIR, "src", "data", "images.ts"), "utf8");
const imagesJs = ts.transpileModule(imagesSource, {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2022,
  },
}).outputText;

const mocks = new Map([
  ["./images", () => ({})],
  ["../data/images", () => ({})],
]);

const moduleObj = { exports: {} };
const sandbox = {
  exports: moduleObj.exports,
  module: moduleObj,
  require(id) {
    const resolved = mocks.get(id);
    if (resolved === undefined) {
      throw new Error(`extract-demo: no mock for import ${id}`);
    }
    return resolved();
  },
  console,
  Date,
  Math,
  Number,
  Object,
  Array,
  String,
  RegExp,
  JSON,
  parseInt,
  parseFloat,
  isNaN,
  isFinite,
};

vm.createContext(sandbox);
vm.runInContext(imagesJs, sandbox, { filename: "images.ts" });
const demoImages = moduleObj.exports.demoImages;

// Evaluate listings.ts in a fresh context whose require mock returns the
// already-evaluated demoImages function.
const listingModule = { exports: {} };
const listingSandbox = {
  exports: listingModule.exports,
  module: listingModule,
  require(id) {
    if (id === "./images" || id === "../data/images") {
      return { demoImages };
    }
    throw new Error(`extract-demo: no mock for import ${id}`);
  },
  console,
  Date,
  Math,
  Number,
  Object,
  Array,
  String,
  RegExp,
  JSON,
  parseInt,
  parseFloat,
  isNaN,
  isFinite,
};
vm.createContext(listingSandbox);
vm.runInContext(js, listingSandbox, { filename: SOURCE });

const listings = listingModule.exports.demoListings;
if (!Array.isArray(listings) || listings.length === 0) {
  console.error("extract-demo: demoListings not found in transpiled module");
  process.exit(1);
}

writeFileSync(OUTPUT, JSON.stringify(listings, null, 2) + "\n");
console.log(`extract-demo: wrote ${listings.length} listings to ${OUTPUT}`);
