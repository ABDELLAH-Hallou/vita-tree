import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { readFileSync, existsSync, readdirSync } from "node:fs";
import { resolve, relative } from "node:path";
import { createHash } from "node:crypto";

const root = process.cwd();
const source = resolve(root, "frontend/src");
const compat = resolve(source, "compat");
const entries = Object.fromEntries(
  readdirSync(compat)
    .filter((file) => file.endsWith(".js") && file !== "app.js")
    .map((file) => [file.slice(0, -3), resolve(compat, file)]),
);
function sourceFiles(directory: string): string[] {
  return readdirSync(directory, { withFileTypes: true }).flatMap((item) =>
    item.isDirectory()
      ? sourceFiles(resolve(directory, item.name))
      : [resolve(directory, item.name)],
  );
}

export default defineConfig({
  root: resolve(root, "frontend"),
  publicDir: resolve(root, "src/vita_tree/static"),
  plugins: [
    {
      name: "vita-portable-source",
      enforce: "pre",
      load(id) {
        const local = relative(source, id);
        if (!local.startsWith("..") && /\.[jt]sx?$/.test(id)) {
          // Template literals must bundle identically on CRLF and LF checkouts.
          return readFileSync(id, "utf8").replaceAll("\r\n", "\n");
        }
      },
    },
    react(),
    {
      name: "vita-offline-assets",
      resolveId(id) {
        if (id.includes("/vendor/"))
          return {
            id: "vita-vendor/" + id.split("/vendor/")[1],
            external: true,
          };
      },
      generateBundle(_options, bundle) {
        const packages = new Map<string, string>();
        for (const chunk of Object.values(bundle)) {
          if (chunk.type !== "chunk") continue;
          for (const id of Object.keys(chunk.modules)) {
            const path = id.replaceAll("\\", "/");
            const marker = path.lastIndexOf("/node_modules/");
            if (marker < 0) continue;
            const tail = path.slice(marker + 14).split("/");
            const name = tail[0].startsWith("@")
              ? tail.slice(0, 2).join("/")
              : tail[0];
            packages.set(name, path.slice(0, marker + 14) + name);
          }
        }
        const notices = [];
        for (const [name, directory] of [...packages].sort(([a], [b]) =>
          a.localeCompare(b),
        )) {
          if (!existsSync(resolve(directory, "package.json"))) continue;
          const metadata = JSON.parse(
            readFileSync(resolve(directory, "package.json"), "utf8"),
          );
          const fallback =
            name === "react-remove-scroll-bar"
              ? resolve(
                  root,
                  "src/vita_tree/static/vendor/FRONTEND-REMOVE-SCROLL-LICENSE",
                )
              : "";
          const license = [
            ...[
              "LICENSE",
              "LICENSE.md",
              "LICENSE.txt",
              "license",
              "license.md",
            ].map((file) => resolve(directory, file)),
            fallback,
          ]
            .filter(Boolean)
            .find(existsSync);
          if (!license) throw new Error("Missing bundled license for " + name);
          const text = readFileSync(license, "utf8").replaceAll("\r\n", "\n");
          if (!text.includes("Copyright") && !text.includes("copyright"))
            throw new Error("Invalid bundled license for " + name);
          notices.push(`${name} ${metadata.version}\n${text}`);
        }
        this.emitFile({
          type: "asset",
          fileName: "vendor/FRONTEND-LICENSE",
          source: notices.join("\n\n"),
        });
        const html = readFileSync(resolve(root, "frontend/index.html"), "utf8")
          .replace(
            'type="module" src="/src/theme-bootstrap.ts"',
            'src="theme.js"',
          )
          .replace('src="/src/main.tsx"', 'src="app.js"')
          .replace(
            "</head>",
            '<link rel="stylesheet" href="styles.css"></head>',
          );
        this.emitFile({ type: "asset", fileName: "index.html", source: html });
        const inputs = [
          ...sourceFiles(resolve(root, "frontend")),
          resolve(root, "vite.config.ts"),
          resolve(root, "tsconfig.json"),
          resolve(root, "package-lock.json"),
        ].sort();
        const sources = Object.fromEntries(
          inputs.map((file) => [
            relative(root, file).replaceAll("\\", "/"),
            createHash("sha256")
              .update(readFileSync(file, "utf8").replaceAll("\r\n", "\n"))
              .digest("hex"),
          ]),
        );
        const files = [
          ...Object.keys(bundle),
          "vendor/FRONTEND-LICENSE",
          "index.html",
          "frontend-manifest.json",
        ]
          .filter((value, index, array) => array.indexOf(value) === index)
          .sort();
        this.emitFile({
          type: "asset",
          fileName: "frontend-manifest.json",
          source:
            JSON.stringify({ schemaVersion: 1, files, sources }, null, 2) +
            "\n",
        });
      },
    },
  ],
  define: { "process.env.NODE_ENV": JSON.stringify("production") },
  build: {
    outDir: resolve(root, "src/vita_tree/static"),
    emptyOutDir: false,
    copyPublicDir: false,
    sourcemap: false,
    target: "es2022",
    lib: {
      entry: {
        app: resolve(source, "main.tsx"),
        theme: resolve(source, "theme-bootstrap.ts"),
        ...entries,
      },
      formats: ["es"],
      cssFileName: "styles",
    },
    cssCodeSplit: false,
    rollupOptions: {
      output: {
        paths: (id) =>
          id.startsWith("vita-vendor/")
            ? "/vendor/" + id.slice("vita-vendor/".length)
            : id,
        entryFileNames: "[name].js",
        chunkFileNames: "assets/frontend-[name]-[hash].js",
        assetFileNames: (asset) =>
          asset.names?.some((name) => name.endsWith(".css"))
            ? "styles.css"
            : "assets/frontend-[name]-[hash][extname]",
      },
    },
  },
});
