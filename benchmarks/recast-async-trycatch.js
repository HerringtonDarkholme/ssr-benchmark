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
let total = 0;
for (const file of files) {
  try {
    const code = fs.readFileSync(file, 'utf8');
    const ast = recast.parse(code, { parser: require('recast/parsers/babel') });
    recast.visit(ast, {
      visitFunctionDeclaration(p) {
        if (p.node.async) {
          let hasTry = false;
          recast.visit(p.node, {
            visitTryStatement() { hasTry = true; return false; }
          });
          if (hasTry) total++;
        }
        this.traverse(p);
      }
    });
  } catch(e) { /* skip */ }
}
process.stdout.write(`Found ${total} async functions with try/catch\n`);
