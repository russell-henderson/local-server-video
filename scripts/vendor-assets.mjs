// Reproducible copies of existing UI dependencies; run after npm ci.
import {mkdir, copyFile, cp, writeFile, readFile} from 'node:fs/promises';
import path from 'node:path';
const output = 'static/vendor';
async function copy(from, to) {
  await mkdir(path.dirname(to), {recursive: true});
  await copyFile(from, to);
}
await copy('node_modules/bootstrap/dist/css/bootstrap.min.css', output + '/bootstrap/bootstrap.min.css');
await copy('node_modules/bootstrap/dist/js/bootstrap.bundle.min.js', output + '/bootstrap/bootstrap.bundle.min.js');
await copy('node_modules/bootstrap/LICENSE', output + '/bootstrap/LICENSE');
await copy('node_modules/@fortawesome/fontawesome-free/css/all.min.css', output + '/fontawesome/css/all.min.css');
await cp('node_modules/@fortawesome/fontawesome-free/webfonts', output + '/fontawesome/webfonts', {recursive: true});
await copy('node_modules/@fortawesome/fontawesome-free/LICENSE.txt', output + '/fontawesome/LICENSE.txt');
await mkdir(output + '/roboto/files', {recursive: true});
let css = '';
for (const weight of [300,400,500,700]) {
  css += await readFile('node_modules/@fontsource/roboto/latin-' + weight + '.css', 'utf8');
  for (const extension of ['woff', 'woff2']) {
    const name = 'roboto-latin-' + weight + '-normal.' + extension;
    await copy('node_modules/@fontsource/roboto/files/' + name, output + '/roboto/files/' + name);
  }
}
await writeFile(output + '/roboto/roboto.css', css);
await copy('node_modules/@fontsource/roboto/LICENSE', output + '/roboto/LICENSE');
