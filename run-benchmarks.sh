#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FIXTURES="$SCRIPT_DIR/fixtures"
RESULTS="$SCRIPT_DIR/results"
BENCHMARKS="$SCRIPT_DIR/benchmarks"
ITERATIONS="${1:-5}"

mkdir -p "$RESULTS"

# Colors
G='\033[0;32m'; Y='\033[0;33m'; C='\033[0;36m'; R='\033[0m'

echo -e "${C}=== AST Tool Benchmark Suite ===${R}"
echo "Fixtures:   $FIXTURES"
echo "Iterations: $ITERATIONS"
echo "Files:      $(find "$FIXTURES" -name '*.js' -o -name '*.ts' | wc -l | tr -d ' ')"
echo ""

# Collect results as CSV
CSVFILE="$RESULTS/results.csv"
echo "tool,task,iteration,real_ms,user_ms,sys_ms,max_rss_kb" > "$CSVFILE"

# GNU time on macOS is gtime, on Linux it's /usr/bin/time
if command -v gtime &>/dev/null; then
  TIME_CMD="gtime"
else
  TIME_CMD="/usr/bin/time"
fi

run_bench() {
  local tool="$1"
  local task="$2"
  shift 2
  local cmd=("$@")

  echo -e "${Y}[$tool] $task${R}"

  for i in $(seq 1 "$ITERATIONS"); do
    # Use /usr/bin/time for memory, bash time for wall clock
    local timefile
    timefile=$(mktemp)

    local start end elapsed_ms
    start=$(python3 -c 'import time; print(int(time.time()*1000))')

    # Run with /usr/bin/time to capture RSS
    $TIME_CMD -l "${cmd[@]}" > /dev/null 2> "$timefile" || true

    end=$(python3 -c 'import time; print(int(time.time()*1000))')
    elapsed_ms=$((end - start))

    # Parse max RSS from macOS /usr/bin/time output (bytes on macOS)
    local rss_kb=0
    if [[ "$(uname)" == "Darwin" ]]; then
      rss_kb=$(grep 'maximum resident set size' "$timefile" | awk '{print $1}' | head -1)
      # macOS reports bytes, convert to KB
      rss_kb=$((rss_kb / 1024))
    else
      rss_kb=$(grep 'Maximum resident' "$timefile" | awk '{print $NF}' | head -1)
    fi
    rss_kb=${rss_kb:-0}

    # Parse user/sys time
    local user_s sys_s
    user_s=$(grep 'user' "$timefile" | head -1 | awk '{print $1}') || user_s="0"
    sys_s=$(grep 'sys' "$timefile" | head -1 | awk '{print $1}') || sys_s="0"
    local user_ms sys_ms
    user_ms=$(python3 -c "print(int(float('${user_s:-0}') * 1000))" 2>/dev/null || echo 0)
    sys_ms=$(python3 -c "print(int(float('${sys_s:-0}') * 1000))" 2>/dev/null || echo 0)

    echo "  iter $i: ${elapsed_ms}ms (RSS: ${rss_kb}KB)"
    echo "$tool,$task,$i,$elapsed_ms,$user_ms,$sys_ms,$rss_kb" >> "$CSVFILE"

    rm -f "$timefile"
  done
  echo ""
}

# ============================================================
# TASK 1: Pattern Search — find all console.log(...) calls
# ============================================================
echo -e "${G}--- Task 1: Search for console.log calls ---${R}"

# ast-grep
run_bench "ast-grep" "search-console-log" \
  ast-grep --pattern 'console.log($$$)' "$FIXTURES"

# semgrep
cat > "$BENCHMARKS/semgrep-console-log.yaml" <<'EOF'
rules:
  - id: console-log
    pattern: console.log(...)
    message: "Found console.log"
    languages: [javascript, typescript]
    severity: INFO
EOF
run_bench "semgrep" "search-console-log" \
  semgrep --config "$BENCHMARKS/semgrep-console-log.yaml" "$FIXTURES" --no-git-ignore --metrics=off

# gritql
run_bench "gritql" "search-console-log" \
  grit patterns test --source 'console.log($args)' "$FIXTURES" 2>/dev/null || \
run_bench "gritql" "search-console-log" \
  grit apply '`console.log($args)`' "$FIXTURES" --dry-run

# jscodeshift (search via transform that counts matches)
cat > "$BENCHMARKS/jscodeshift-search-console-log.js" <<'JSEOF'
module.exports = function(fileInfo, api) {
  const j = api.jscodeshift;
  const root = j(fileInfo.source);
  const count = root.find(j.CallExpression, {
    callee: { object: { name: 'console' }, property: { name: 'log' } }
  }).length;
  return fileInfo.source; // no changes
};
JSEOF
run_bench "jscodeshift" "search-console-log" \
  npx jscodeshift --dry --silent -t "$BENCHMARKS/jscodeshift-search-console-log.js" "$FIXTURES"

# recast (custom Node script)
cat > "$BENCHMARKS/recast-search-console-log.js" <<'JSEOF'
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
      visitCallExpression(p) {
        const c = p.node.callee;
        if (c.type === 'MemberExpression' && c.object.name === 'console' && c.property.name === 'log') {
          total++;
        }
        this.traverse(p);
      }
    });
  } catch(e) { /* skip unparseable files */ }
}
process.stdout.write(`Found ${total} console.log calls\n`);
JSEOF
run_bench "recast" "search-console-log" \
  node "$BENCHMARKS/recast-search-console-log.js" "$FIXTURES"


# ============================================================
# TASK 2: Transform — convert var → const
# ============================================================
echo -e "${G}--- Task 2: Transform var → const ---${R}"

# We work on copies to avoid mutating fixtures between runs
make_copy() {
  local copy="$RESULTS/fixtures_copy_$1"
  rm -rf "$copy"
  cp -r "$FIXTURES" "$copy"
  echo "$copy"
}

# ast-grep (using --rewrite)
COPY=$(make_copy ast-grep-var)
run_bench "ast-grep" "transform-var-to-const" \
  ast-grep --pattern 'var $NAME = $INIT' --rewrite 'const $NAME = $INIT' "$COPY" --update-all

# semgrep (autofix)
cat > "$BENCHMARKS/semgrep-var-to-const.yaml" <<'EOF'
rules:
  - id: var-to-const
    pattern: var $X = $Y;
    fix: const $X = $Y;
    message: "Convert var to const"
    languages: [javascript, typescript]
    severity: INFO
EOF
COPY=$(make_copy semgrep-var)
run_bench "semgrep" "transform-var-to-const" \
  semgrep --config "$BENCHMARKS/semgrep-var-to-const.yaml" "$COPY" --autofix --no-git-ignore --metrics=off

# gritql
COPY=$(make_copy gritql-var)
run_bench "gritql" "transform-var-to-const" \
  grit apply '`var $name = $init` => `const $name = $init`' "$COPY"

# jscodeshift
cat > "$BENCHMARKS/jscodeshift-var-to-const.js" <<'JSEOF'
module.exports = function(fileInfo, api) {
  const j = api.jscodeshift;
  const root = j(fileInfo.source);
  root.find(j.VariableDeclaration, { kind: 'var' })
    .forEach(p => { p.node.kind = 'const'; });
  return root.toSource();
};
JSEOF
COPY=$(make_copy jscodeshift-var)
run_bench "jscodeshift" "transform-var-to-const" \
  npx jscodeshift --silent -t "$BENCHMARKS/jscodeshift-var-to-const.js" "$COPY"

# recast
cat > "$BENCHMARKS/recast-var-to-const.js" <<'JSEOF'
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
JSEOF
COPY=$(make_copy recast-var)
run_bench "recast" "transform-var-to-const" \
  node "$BENCHMARKS/recast-var-to-const.js" "$COPY"


# ============================================================
# TASK 3: Complex Pattern — find async methods with try/catch
# ============================================================
echo -e "${G}--- Task 3: Search for async functions with try/catch ---${R}"

# ast-grep
run_bench "ast-grep" "search-async-trycatch" \
  ast-grep --pattern 'async function $NAME($$$) { $$$ try { $$$ } catch($ERR) { $$$ } $$$ }' "$FIXTURES"

# semgrep
cat > "$BENCHMARKS/semgrep-async-trycatch.yaml" <<'EOF'
rules:
  - id: async-trycatch
    pattern: |
      async function $F(...) {
        ...
        try { ... } catch ($E) { ... }
        ...
      }
    message: "async function with try/catch"
    languages: [javascript, typescript]
    severity: INFO
EOF
run_bench "semgrep" "search-async-trycatch" \
  semgrep --config "$BENCHMARKS/semgrep-async-trycatch.yaml" "$FIXTURES" --no-git-ignore --metrics=off

# gritql
run_bench "gritql" "search-async-trycatch" \
  grit apply '`async function $name($args) { $body }` where { $body <: contains `try { $_ } catch($e) { $_ }` }' "$FIXTURES" --dry-run

# jscodeshift
cat > "$BENCHMARKS/jscodeshift-async-trycatch.js" <<'JSEOF'
module.exports = function(fileInfo, api) {
  const j = api.jscodeshift;
  const root = j(fileInfo.source);
  root.find(j.FunctionDeclaration, { async: true })
    .filter(p => {
      let hasTryCatch = false;
      j(p).find(j.TryStatement).forEach(() => { hasTryCatch = true; });
      return hasTryCatch;
    });
  return fileInfo.source;
};
JSEOF
run_bench "jscodeshift" "search-async-trycatch" \
  npx jscodeshift --dry --silent -t "$BENCHMARKS/jscodeshift-async-trycatch.js" "$FIXTURES"

# recast
cat > "$BENCHMARKS/recast-async-trycatch.js" <<'JSEOF'
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
JSEOF
run_bench "recast" "search-async-trycatch" \
  node "$BENCHMARKS/recast-async-trycatch.js" "$FIXTURES"


# ============================================================
# Summary
# ============================================================
echo -e "${C}=== Results saved to $CSVFILE ===${R}"
echo ""

# Print summary table
echo -e "${G}=== Summary (median real_ms per task) ===${R}"
python3 "$SCRIPT_DIR/summarize.py" "$CSVFILE"
