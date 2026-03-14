#!/usr/bin/env python3
"""Generate a beautiful benchmark comparison chart."""
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# ── Data ──────────────────────────────────────────────────────────
tools = ['ast-grep', 'GritQL', 'recast', 'jscodeshift', 'semgrep']

tasks = {
    'Search console.log': [43, 80, 200, 754, 7535],
    'Transform var → const': [41, 816, 200, 808, 13111],
    'Search async + try/catch': [44, 1486, 199, 764, 1433],
}

memory = {
    'Search console.log': [11, 58, 93, 153, 250],
    'Transform var → const': [10, 57, 95, 157, 327],
    'Search async + try/catch': [11, 58, 95, 154, 231],
}

# ── Colors ────────────────────────────────────────────────────────
colors = ['#3b82f6', '#22c55e', '#a855f7', '#f59e0b', '#ef4444']
bg_color = '#0f172a'
card_color = '#1e293b'
text_color = '#e2e8f0'
grid_color = '#334155'
accent_color = '#94a3b8'

# ── Figure ────────────────────────────────────────────────────────
fig = plt.figure(figsize=(18, 11), facecolor=bg_color)

# Title — plenty of room at top
fig.text(0.5, 0.98, 'AST Tool Benchmark', ha='center', va='top',
         fontsize=30, fontweight='bold', color=text_color,
         fontfamily='sans-serif')
fig.text(0.5, 0.945, '500 files  ·  75,000 lines  ·  median of 3 runs  ·  Apple Silicon',
         ha='center', va='top', fontsize=14, color=accent_color,
         fontfamily='sans-serif')

task_names = list(tasks.keys())
n_tools = len(tools)
bar_height = 0.52

# Use gridspec for precise control
gs = fig.add_gridspec(2, 3, left=0.08, right=0.96, top=0.87, bottom=0.06,
                      hspace=0.45, wspace=0.35)

# ── Top row: 3 task charts ───────────────────────────────────────
for col, task in enumerate(task_names):
    ax = fig.add_subplot(gs[0, col])
    ax.set_facecolor(card_color)

    times = tasks[task]
    y_pos = np.arange(n_tools)

    bars = ax.barh(y_pos, times, height=bar_height, color=colors,
                   edgecolor='none', zorder=3)

    for bar, c in zip(bars, colors):
        bar.set_linewidth(0)

    # Value labels — always outside the bar
    for i, t in enumerate(times):
        ax.text(t * 1.15, i, f'{t:,}ms',
                ha='left', va='center', fontsize=11,
                fontweight='bold', color=colors[i], fontfamily='sans-serif')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(tools, fontsize=12, color=text_color, fontfamily='sans-serif')
    ax.invert_yaxis()

    ax.set_title(task, fontsize=15, fontweight='bold', color=text_color,
                 fontfamily='sans-serif', pad=14)

    ax.set_xscale('log')
    ax.set_xlim(20, max(times) * 6)
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{int(x):,}'))
    ax.tick_params(axis='x', colors=accent_color, labelsize=9)
    ax.tick_params(axis='y', length=0)

    ax.set_xlabel('Time (ms, log scale)', fontsize=10, color=accent_color,
                  fontfamily='sans-serif')

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color(grid_color)
    ax.spines['left'].set_visible(False)
    ax.grid(axis='x', color=grid_color, linewidth=0.5, zorder=0)

# ── Bottom left: Memory chart ────────────────────────────────────
ax_mem = fig.add_subplot(gs[1, 0])
ax_mem.set_facecolor(card_color)

avg_mem = [np.mean([memory[t][i] for t in task_names]) for i in range(n_tools)]
y_pos = np.arange(n_tools)

bars = ax_mem.barh(y_pos, avg_mem, height=bar_height, color=colors,
                   edgecolor='none', zorder=3)

for i, m in enumerate(avg_mem):
    ax_mem.text(m + max(avg_mem) * 0.04, i, f'{m:.0f} MB',
                ha='left', va='center', fontsize=11,
                fontweight='bold', color=colors[i], fontfamily='sans-serif')

ax_mem.set_yticks(y_pos)
ax_mem.set_yticklabels(tools, fontsize=12, color=text_color, fontfamily='sans-serif')
ax_mem.invert_yaxis()
ax_mem.set_title('Peak Memory (avg across tasks)', fontsize=15, fontweight='bold',
                 color=text_color, fontfamily='sans-serif', pad=14)
ax_mem.set_xlim(0, max(avg_mem) * 1.5)
ax_mem.tick_params(axis='x', colors=accent_color, labelsize=9)
ax_mem.tick_params(axis='y', length=0)
ax_mem.set_xlabel('Memory (MB)', fontsize=10, color=accent_color, fontfamily='sans-serif')
ax_mem.spines['top'].set_visible(False)
ax_mem.spines['right'].set_visible(False)
ax_mem.spines['bottom'].set_color(grid_color)
ax_mem.spines['left'].set_visible(False)
ax_mem.grid(axis='x', color=grid_color, linewidth=0.5, zorder=0)

# ── Bottom center: Speedup multiplier chart ──────────────────────
ax_sp = fig.add_subplot(gs[1, 1])
ax_sp.set_facecolor(card_color)

geo_means = []
for i in range(n_tools):
    ratios = [tasks[t][i] / tasks[t][0] for t in task_names]
    geo = np.exp(np.mean(np.log(ratios)))
    geo_means.append(geo)

y_pos = np.arange(n_tools)
bars = ax_sp.barh(y_pos, geo_means, height=bar_height, color=colors,
                  edgecolor='none', zorder=3)

for i, g in enumerate(geo_means):
    label = f'{g:.0f}x' if g >= 2 else f'{g:.1f}x'
    ax_sp.text(g + max(geo_means) * 0.03, i, label,
               ha='left', va='center', fontsize=12,
               fontweight='bold', color=colors[i], fontfamily='sans-serif')

ax_sp.set_yticks(y_pos)
ax_sp.set_yticklabels(tools, fontsize=12, color=text_color, fontfamily='sans-serif')
ax_sp.invert_yaxis()
ax_sp.set_title('Slowdown vs ast-grep (geometric mean)', fontsize=15, fontweight='bold',
                color=text_color, fontfamily='sans-serif', pad=14)
ax_sp.set_xlim(0, max(geo_means) * 1.35)
ax_sp.tick_params(axis='x', colors=accent_color, labelsize=9)
ax_sp.tick_params(axis='y', length=0)
ax_sp.set_xlabel('Times slower', fontsize=10, color=accent_color, fontfamily='sans-serif')
ax_sp.spines['top'].set_visible(False)
ax_sp.spines['right'].set_visible(False)
ax_sp.spines['bottom'].set_color(grid_color)
ax_sp.spines['left'].set_visible(False)
ax_sp.grid(axis='x', color=grid_color, linewidth=0.5, zorder=0)

# ── Bottom right: Key takeaways ──────────────────────────────────
ax_info = fig.add_subplot(gs[1, 2])
ax_info.set_facecolor(card_color)
ax_info.set_xlim(0, 10)
ax_info.set_ylim(0, 10)
ax_info.axis('off')

# Rounded border effect
for spine in ax_info.spines.values():
    spine.set_visible(False)

takeaways = [
    ('●', colors[0], 'ast-grep: ~42ms avg, 11 MB peak'),
    ('●', colors[0], '5x faster than next fastest tool'),
    ('●', colors[0], 'No slowdown on complex patterns'),
    ('', '', ''),
    ('●', colors[1], 'GritQL: fast search, slower transforms'),
    ('●', colors[2], 'recast: consistent ~200ms baseline'),
    ('●', colors[3], 'jscodeshift: worker overhead (~770ms)'),
    ('●', colors[4], 'semgrep: built for CI, not speed'),
]

ax_info.text(0.3, 9.5, 'Key Takeaways', fontsize=16, fontweight='bold',
             color=text_color, fontfamily='sans-serif', va='top')

for i, (bullet, color, text) in enumerate(takeaways):
    y = 8.2 - i * 1.05
    if bullet:
        ax_info.text(0.3, y, bullet, fontsize=14, color=color,
                     fontfamily='sans-serif', va='center')
        ax_info.text(1.1, y, text, fontsize=12, color=text_color,
                     fontfamily='sans-serif', va='center')

# ── Save ──────────────────────────────────────────────────────────
fig.savefig('benchmark.png', dpi=200,
            facecolor=bg_color, bbox_inches='tight', pad_inches=0.4)
print('Saved benchmark.png')
