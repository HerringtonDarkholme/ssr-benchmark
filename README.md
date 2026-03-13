# How Fast Is Your Code Search Tool? A Benchmark of Five AST Tools

Every codebase has patterns you need to find. Maybe it's leftover `console.log` calls before a release. Maybe you need to rename a variable across hundreds of files. Or find every function that handles errors a certain way.

You could use find-and-replace — but that only matches text. It doesn't understand code. A text search for `log` will match variable names, comments, and URLs. What you really want is a tool that understands the *structure* of your code — one that knows the difference between a function call and a variable name.

These are called **structural code search tools**. They parse your code into a tree (called an Abstract Syntax Tree, or AST), then let you match against the shape of the code rather than its raw text. Some of them can also *rewrite* code — replacing patterns across hundreds of files in one shot.

There are several popular options in this space:

- **[ast-grep](https://ast-grep.github.io/)** — a command-line tool written in Rust. You describe the code pattern you're looking for using something that looks like the code itself.
- **[GritQL](https://docs.grit.io/)** — another Rust-based tool with its own query language for matching and rewriting code.
- **[semgrep](https://semgrep.dev/)** — a widely-used code scanning tool, popular for security analysis in CI pipelines.
- **[jscodeshift](https://github.com/facebook/jscodeshift)** — Facebook's toolkit for large-scale code changes. You write transforms in JavaScript.
- **[recast](https://github.com/benjamn/recast)** — a JavaScript library for parsing and modifying code while preserving formatting. Powers jscodeshift under the hood.

They all solve the same core problem, but they're built very differently — different languages, different architectures, different design goals. I wanted to know: **how do they actually compare in performance?**

I put all five to the test — and the results weren't even close.

## The Bottom Line

Here's what happened when I asked each tool to search and transform 500 files:

```
Speed                              Memory

ast-grep  ██ 43ms                  ast-grep  ██ 11 MB
recast    ██████ 200ms             GritQL    ██████████ 58 MB
GritQL    ████████████ 794ms       recast    ████████████████ 94 MB
jscodeshift ████████████ 775ms     jscodeshift █████████████████████████ 155 MB
semgrep   ██████████████████████   semgrep   ████████████████████████████████████
          7,360ms                             269 MB
```

**ast-grep is 5x faster than the next fastest tool** and uses a fraction of the memory. It processed 500 files in roughly the time it takes you to blink.

**The speed gap widens, not narrows, on harder tasks.** While other tools slow down on complex patterns, ast-grep stays flat around 42ms. It has headroom that the others don't.

**Memory tells a story too.** ast-grep peaks at 11 MB. semgrep uses 25x more. If you're running these tools in CI pipelines, editor plugins, or git hooks — that overhead adds up.

Now let me show you how I got here.

## How I Tested

I generated **500 JavaScript and TypeScript files** — about **75,000 lines of code** in total. Realistic stuff: classes, functions, imports, error handling, the kind of code you'd find in a real project.

Then I ran three tasks, each designed to test a different kind of workload:

1. **Simple search** — find every `console.log(...)` call
2. **Code transformation** — change every `var` to `const` across all files
3. **Complex search** — find async functions that contain try/catch blocks

Each task was run 3 times. I took the median to avoid flukes. All benchmarks run on Apple Silicon.

## The Results, Task by Task

### Task 1: Find every `console.log`

| Tool | Time | Memory Used |
|------|-----:|------------:|
| **ast-grep** | **43 ms** | **11 MB** |
| GritQL | 80 ms | 58 MB |
| recast | 200 ms | 93 MB |
| jscodeshift | 754 ms | 153 MB |
| semgrep | 7,535 ms | 250 MB |

ast-grep scans all 500 files in 43 milliseconds — **faster than a single frame of video**. By the time semgrep finishes 7.5 seconds later, you could have run ast-grep **175 times**.

### Task 2: Replace `var` with `const` in every file

| Tool | Time | Memory Used |
|------|-----:|------------:|
| **ast-grep** | **41 ms** | **10 MB** |
| recast | 200 ms | 95 MB |
| jscodeshift | 808 ms | 157 MB |
| GritQL | 816 ms | 57 MB |
| semgrep | 13,111 ms | 327 MB |

This isn't just reading — it's rewriting 500 files. ast-grep does it in 41 milliseconds, using just 10 MB of memory. semgrep needs **13 seconds** and **327 MB** for the same job.

### Task 3: Find async functions with error handling

A harder pattern: find functions marked `async` that contain a `try/catch` block inside them.

| Tool | Time | Memory Used |
|------|-----:|------------:|
| **ast-grep** | **44 ms** | **11 MB** |
| recast | 199 ms | 95 MB |
| jscodeshift | 764 ms | 154 MB |
| semgrep | 1,433 ms | 231 MB |
| GritQL | 1,486 ms | 58 MB |

The pattern is more complex, but ast-grep doesn't slow down. 44 ms — essentially the same speed as the simple search. The other tools take noticeably longer as the query gets harder.

## Why Is ast-grep So Fast?

Without getting too deep into the technical weeds:

**It's built on a very fast parser.** ast-grep uses [tree-sitter](https://tree-sitter.github.io/), a parsing library originally built for code editors like VS Code and Neovim. Tree-sitter is designed to parse code in real-time as you type — so parsing 500 files in batch is trivial for it.

**It's written in Rust.** Rust compiles to native machine code with no runtime overhead. There's no interpreter starting up, no virtual machine warming up — just raw execution.

**It does one thing well.** ast-grep is focused on structural search and replace. It doesn't run security analysis, manage rule databases, or coordinate worker processes. That focus translates directly to speed.

The other tools make different tradeoffs:

- **GritQL** also uses tree-sitter and Rust, so simple searches are nearly as fast. But its richer query language adds overhead for complex patterns and rewrites.
- **recast** is a JavaScript library — it has to start a Node.js runtime and parse files through a full JavaScript compiler (Babel). The ~200ms it consistently achieves is actually impressive for that stack.
- **jscodeshift** wraps recast but adds worker process management on top. Good for massive codebases with thousands of files, but the coordination overhead hurts at smaller scale.
- **semgrep** is built for a different job: scanning code for security vulnerabilities and enforcing rules in CI. It's loading an entire analysis engine, which is overkill for a single pattern search.

## What This Means in Practice

These numbers aren't just academic. Speed changes how you use a tool:

- **At 40ms**, you can run ast-grep on every keystroke in your editor. It's instant feedback.
- **At 200ms**, recast is fine for a script you run occasionally.
- **At 800ms**, jscodeshift feels like a build step — you run it and wait.
- **At 7-13 seconds**, semgrep is something you run in CI, not interactively.

If you're building a git hook that checks for patterns before every commit, the difference between 40ms and 7 seconds is the difference between invisible and annoying.

If you're integrating code search into an editor or IDE, 40ms means real-time results. 800ms means a loading spinner.

## Try It Yourself

The full benchmark code is open source at [github.com/HerringtonDarkholme/ssr-benchmark](https://github.com/HerringtonDarkholme/ssr-benchmark). You can run it on your own machine:

```bash
# Generate 500 test files
node generate-fixtures.js 500 150

# Run benchmarks (3 iterations)
bash run-benchmarks.sh 3
```

Scale it up if you want — try 2,000 files or 5,000. The gaps only get wider.

---

*Results will vary by machine, but relative rankings are consistent. Each tool was tested at its latest stable version as of March 2026.*

*Disclaimer: I am the author of ast-grep. I've done my best to make this benchmark fair — all tools were tested with the same corpus, the same tasks, and the same methodology. The benchmark code is [open source](https://github.com/HerringtonDarkholme/ssr-benchmark) so you can verify and reproduce the results yourself.*
