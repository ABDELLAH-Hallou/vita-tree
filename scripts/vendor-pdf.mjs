import { cp, mkdir } from 'node:fs/promises';
const dest = 'src/vita_tree/static/vendor';
await mkdir(dest, { recursive: true });
for (const name of ['pdf.mjs', 'pdf.worker.mjs']) {
  await cp(`node_modules/pdfjs-dist/build/${name}`, `${dest}/${name}`);
}
await cp('node_modules/pdfjs-dist/web/pdf_viewer.css', `${dest}/pdf_viewer.css`);
await cp('node_modules/pdfjs-dist/LICENSE', `${dest}/PDFJS-LICENSE`);
for (const dir of ['standard_fonts', 'cmaps', 'wasm']) {
  await cp(`node_modules/pdfjs-dist/${dir}`, `${dest}/${dir}`, { recursive: true });
}
