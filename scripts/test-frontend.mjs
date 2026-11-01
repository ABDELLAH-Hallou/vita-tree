import { build } from "esbuild";
import { readdirSync } from "node:fs";
import { resolve } from "node:path";
import { spawnSync } from "node:child_process";

const files = readdirSync("frontend/tests").filter((file) =>
  /\.test\.tsx?$/.test(file),
);
const output = resolve(".test-artifacts/frontend-tests");
await build({
  entryPoints: files.map((file) => "frontend/tests/" + file),
  outdir: output,
  bundle: true,
  platform: "node",
  packages: "external",
  format: "esm",
  jsx: "automatic",
  target: "node24",
});
const result = spawnSync(
  process.execPath,
  [
    "--test",
    ...files.map((file) => resolve(output, file.replace(/\.tsx?$/, ".js"))),
  ],
  { stdio: "inherit" },
);
if (result.error) throw result.error;
process.exitCode = result.status ?? 1;
