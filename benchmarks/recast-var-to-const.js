const fs = require('fs');
const path = require('path');
const recast = require('recast');

function walk(dir) {
  const files = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) files.push(...walk(full));
    else if (/\.[jt]s$/.test(entry.name)) files.push(full);
  }
  return files;
}

const files = walk(process.argv[2]);
let changed = 0;
for (const file of files) {
  try {
    const code = fs.readFileSync(file, 'utf8');
    const ast = recast.parse(code, { parser: require('recast/parsers/babel') });
    let modified = false;
    recast.visit(ast, {
      visitVariableDeclaration(p) {
        if (p.node.kind === 'var') {
          p.node.kind = 'const';
          modified = true;
        }
        this.traverse(p);
      }
    });
    if (modified) {
      fs.writeFileSync(file, recast.print(ast).code);
      changed++;
    }
  } catch(e) { /* skip */ }
}
process.stdout.write(`Changed ${changed} files\n`);
