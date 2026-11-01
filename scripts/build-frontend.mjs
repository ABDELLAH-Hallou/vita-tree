import { readFileSync, existsSync, unlinkSync } from "node:fs";
import { resolve, relative, isAbsolute } from "node:path";
import { build } from "vite";

const root = resolve("src/vita_tree/static");
const manifest = resolve(root, "frontend-manifest.json");
if (existsSync(manifest)) {
  for (const name of JSON.parse(readFileSync(manifest, "utf8")).files) {
    const target = resolve(root, name),
      local = relative(root, target);
    if (
      isAbsolute(local) ||
      local.startsWith("..") ||
      (name.startsWith("vendor/") && name !== "vendor/FRONTEND-LICENSE")
    )
      throw new Error("Unsafe generated frontend path");
    if (existsSync(target)) unlinkSync(target);
  }
}
await build(process.argv.includes("--watch") ? { build: { watch: {} } } : {});
