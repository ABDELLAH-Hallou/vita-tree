import {build} from 'esbuild';
import {readFile, writeFile} from 'node:fs/promises';

const result = await build({
  entryPoints: ['scripts/latex-editor.mjs'],
  outfile: 'src/vita_tree/static/vendor/editor.mjs',
  bundle: true, format: 'esm', target: 'es2022', minify: true,
  legalComments: 'inline', metafile: true,
});
const packages = new Set(Object.keys(result.metafile.inputs)
  .filter(path => path.startsWith('node_modules/'))
  .map(path => path.split('/').slice(1, path.split('/')[1].startsWith('@') ? 3 : 2).join('/')));
const notices = [];
for (const name of [...packages].sort()) {
  const dir = `node_modules/${name}`;
  const metadata = JSON.parse(await readFile(`${dir}/package.json`, 'utf8'));
  const license = await readFile(`${dir}/LICENSE`, 'utf8');
  notices.push(`${name} ${metadata.version}\n${license}`);
}
await writeFile('src/vita_tree/static/vendor/EDITOR-LICENSE', notices.join('\n\n'));
console.log(`Bundled offline editor with ${packages.size} dependency license notices.`);
