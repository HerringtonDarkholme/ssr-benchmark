#!/usr/bin/env node
// Generates a realistic corpus of JS/TS files for benchmarking AST tools.
// Usage: node generate-fixtures.js [fileCount] [linesPerFile]

const fs = require('fs');
const path = require('path');

const FILE_COUNT = parseInt(process.argv[2] || '500', 10);
const LINES_PER_FILE = parseInt(process.argv[3] || '150', 10);
const OUT_DIR = path.join(__dirname, 'fixtures');

fs.rmSync(OUT_DIR, { recursive: true, force: true });
fs.mkdirSync(OUT_DIR, { recursive: true });

const classNames = ['UserService', 'OrderManager', 'PaymentProcessor', 'AuthHandler',
  'DataStore', 'CacheLayer', 'EventBus', 'Logger', 'Router', 'Validator',
  'Serializer', 'Middleware', 'Controller', 'Repository', 'Factory'];

const varNames = ['data', 'result', 'items', 'config', 'options', 'payload',
  'response', 'request', 'context', 'state', 'cache', 'buffer'];

const funcNames = ['handleRequest', 'processData', 'validateInput', 'transformOutput',
  'fetchRecords', 'updateState', 'computeHash', 'serializePayload', 'parseConfig',
  'initModule', 'cleanupResources', 'notifyListeners'];

function pick(arr) { return arr[Math.floor(Math.random() * arr.length)]; }
function randInt(min, max) { return Math.floor(Math.random() * (max - min + 1)) + min; }

function generateFile(index) {
  const isTS = index % 3 === 0;
  const ext = isTS ? '.ts' : '.js';
  const lines = [];

  // Imports
  lines.push(`import { ${pick(classNames)} } from './${pick(classNames).toLowerCase()}';`);
  lines.push(`import { ${pick(funcNames)} } from '../utils/${pick(funcNames)}';`);
  if (isTS) lines.push(`import type { Config, Options } from '../types';`);
  lines.push('');

  // Some top-level vars with var/let/const mix
  for (let i = 0; i < randInt(2, 5); i++) {
    const decl = pick(['var', 'let', 'const']);
    const name = pick(varNames) + i;
    if (isTS) {
      lines.push(`${decl} ${name}: ${pick(['string', 'number', 'boolean', 'any'])} = ${decl === 'const' ? JSON.stringify(pick(['hello', 42, true, null])) : 'undefined'};`);
    } else {
      lines.push(`${decl} ${name} = ${JSON.stringify(pick(['hello', 42, true, null]))};`);
    }
  }
  lines.push('');

  // console.log statements (search target)
  for (let i = 0; i < randInt(3, 8); i++) {
    lines.push(`console.log('${pick(varNames)}: ', ${pick(varNames)}${randInt(0, 4)});`);
  }
  lines.push('');

  // Function declarations
  for (let f = 0; f < randInt(2, 5); f++) {
    const fname = pick(funcNames) + f;
    const params = isTS
      ? `(${pick(varNames)}: ${pick(['string', 'number', 'any'])}, ${pick(varNames)}Opt?: ${pick(['boolean', 'object'])})`
      : `(${pick(varNames)}, ${pick(varNames)}Opt)`;

    if (Math.random() > 0.5) {
      // Arrow function
      lines.push(`const ${fname} = ${isTS ? params + ': ' + pick(['void', 'string', 'Promise<void>']) : params} => {`);
    } else {
      // Regular function
      lines.push(`function ${fname}${params} {`);
    }

    // Body
    lines.push(`  const ${pick(varNames)} = ${pick(varNames)}${randInt(0, 4)};`);
    lines.push(`  console.log('${fname}', ${pick(varNames)});`);

    // if statement
    lines.push(`  if (${pick(varNames)}) {`);
    lines.push(`    return ${pick(varNames)};`);
    lines.push(`  }`);

    // try/catch
    if (Math.random() > 0.5) {
      lines.push(`  try {`);
      lines.push(`    await ${pick(funcNames)}(${pick(varNames)});`);
      lines.push(`  } catch (err) {`);
      lines.push(`    console.error('Error in ${fname}:', err);`);
      lines.push(`  }`);
    }

    lines.push(`  return null;`);
    lines.push(`}`);
    lines.push('');
  }

  // Class definition
  const className = pick(classNames) + index;
  lines.push(`class ${className} {`);
  if (isTS) {
    lines.push(`  private ${pick(varNames)}: ${pick(['string', 'number', 'Map<string, any>'])};`);
    lines.push(`  public ${pick(varNames)}List: ${pick(['string[]', 'number[]', 'any[]'])};`);
  }
  lines.push(`  constructor(${isTS ? `private config: Config` : 'config'}) {`);
  lines.push(`    this.config = config;`);
  lines.push(`    console.log('${className} initialized');`);
  lines.push(`  }`);
  lines.push('');

  for (let m = 0; m < randInt(3, 6); m++) {
    const mname = pick(funcNames);
    const asyncKw = Math.random() > 0.5 ? 'async ' : '';
    lines.push(`  ${asyncKw}${mname}(${pick(varNames)}) {`);
    lines.push(`    var temp = ${pick(varNames)};`);
    lines.push(`    let ${pick(varNames)}Result = null;`);
    lines.push(`    console.log('${className}.${mname}');`);
    if (asyncKw) {
      lines.push(`    const ${pick(varNames)} = await this.${pick(funcNames)}(temp);`);
    }
    lines.push(`    if (!${pick(varNames)}) {`);
    lines.push(`      throw new Error('Invalid ${pick(varNames)}');`);
    lines.push(`    }`);
    lines.push(`    return ${pick(varNames)}Result;`);
    lines.push(`  }`);
    lines.push('');
  }

  lines.push(`}`);
  lines.push('');
  lines.push(`export default ${className};`);
  lines.push(`export { ${className} };`);

  // Pad to target line count
  while (lines.length < LINES_PER_FILE) {
    lines.push(`// ${pick(classNames)} - ${pick(funcNames)} - line padding`);
  }

  const subdir = `module${index % 10}`;
  const dir = path.join(OUT_DIR, subdir);
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, `file${index}${ext}`), lines.join('\n'));
}

for (let i = 0; i < FILE_COUNT; i++) {
  generateFile(i);
}

const totalFiles = FILE_COUNT;
const totalLines = FILE_COUNT * LINES_PER_FILE;
console.log(`Generated ${totalFiles} files (~${totalLines} lines) in ${OUT_DIR}`);
