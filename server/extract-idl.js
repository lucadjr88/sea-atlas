// Estrae le IDL da sly.js (righe di `const xxxIDL = {...}`) in JSON.
const fs = require('fs');
const vm = require('vm');
const src = fs.readFileSync('/home/luca/sly/SLY_7.36mio.js', 'utf8').split('\n');
for (const name of ['sageIDL', 'profileIDL']) {
  const line = src.find(l => l.trimStart().startsWith(`const ${name} =`));
  const expr = line.slice(line.indexOf('=') + 1).trim().replace(/;$/, '');
  const idl = vm.runInNewContext(`(${expr})`);
  fs.writeFileSync(`idl/${name.replace('IDL', '')}.json`, JSON.stringify(idl));
  console.log(name, Object.keys(idl).join(','));
}
