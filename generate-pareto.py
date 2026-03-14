#!/usr/bin/env python3
"""Generate a bubble chart: x=time, y=tool, bubble size=log(memory), shape=task."""
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# ── Data ─────────────────────────────────────────────────────────
tools = ['ast-grep', 'GritQL', 'recast', 'jscodeshift', 'semgrep']
colors = ['#3b82f6', '#22c55e', '#a855f7', '#f59e0b', '#ef4444']

tasks = ['Search', 'Transform', 'Complex Search']
task_markers = ['o', 's', 'D']

# (time_ms, memory_mb) per tool per task
data = {
    'Search':         [(43,11), (80,58), (200,93), (754,153), (7535,250)],
    'Transform':      [(41,10), (816,57), (200,95), (808,157), (13111,327)],
    'Complex Search': [(44,11), (1486,58), (199,95), (764,154), (1433,231)],
}

# ── Style ─────────────────────────────────────────────────────────
bg_color = '#0f172a'
card_color = '#1e293b'
text_color = '#e2e8f0'
grid_color = '#334155'
accent_color = '#94a3b8'

fig, ax = plt.subplots(figsize=(14, 7), facecolor=bg_color)
ax.set_facecolor(card_color)

# Log-scale bubble size: map log(memory) to point area
def mem_to_size(mb):
    return (np.log10(mb) / np.log10(400)) * 1200 + 60

n_tools = len(tools)
y_pos = np.arange(n_tools)

# Vertical offsets so 3 task shapes don't overlap per tool row
task_offsets = [-0.22, 0.0, 0.22]

for j, task in enumerate(tasks):
    pts = data[task]
    for i, (t, m) in enumerate(pts):
        s = mem_to_size(m)
        y = i + task_offsets[j]
        ax.scatter(t, y, s=s, color=colors[i], alpha=0.8,
                   marker=task_markers[j], edgecolors='white',
                   linewidths=1.2, zorder=4)

# Tool labels on y-axis
ax.set_yticks(y_pos)
ax.set_yticklabels(tools, fontsize=14, fontweight='bold',
                   color=text_color, fontfamily='sans-serif')
ax.set_ylim(-0.5, n_tools - 0.5)
ax.invert_yaxis()

ax.set_xscale('log')
ax.set_xlim(25, 20000)
ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{int(x):,}'))
ax.tick_params(axis='x', colors=accent_color, labelsize=11)
ax.tick_params(axis='y', length=0)

ax.set_xlabel('Time (ms, log scale) — faster is better', fontsize=13,
              color=text_color, fontfamily='sans-serif', labelpad=10)

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_color(grid_color)
ax.spines['left'].set_visible(False)
ax.grid(axis='x', color=grid_color, linewidth=0.5, alpha=0.5, zorder=0)

# ── Title ────────────────────────────────────────────────────────
fig.text(0.5, 0.97, 'AST Tool Benchmark: Speed & Memory', ha='center', va='top',
         fontsize=24, fontweight='bold', color=text_color, fontfamily='sans-serif')
fig.text(0.5, 0.935, 'Bubble size = peak memory (log scale). Shape = task type.',
         ha='center', va='top', fontsize=13, color=accent_color, fontfamily='sans-serif')

# ── Legend: task shapes ──────────────────────────────────────────
for j, (task, mk) in enumerate(zip(tasks, task_markers)):
    lx = 0.75 + j * 0.09
    ax.scatter([], [], marker=mk, s=100, color=accent_color,
               edgecolors='white', linewidths=1, label=task)

leg = ax.legend(loc='lower right', fontsize=12, frameon=True,
                facecolor=card_color, edgecolor=grid_color,
                labelcolor=text_color, borderpad=0.8,
                handletextpad=0.5, columnspacing=1.5, ncol=3)

# ── Bubble size legend ───────────────────────────────────────────
legend_mems = [10, 50, 150, 300]
bx_start = 0.13
for k, mem in enumerate(legend_mems):
    bx = bx_start + k * 0.065
    s = mem_to_size(mem)
    ax.scatter(32, -0.5 + k * 0, s=0, color='none')  # dummy
    fig.text(bx, 0.06, f'{mem}', ha='center', fontsize=10,
             color=accent_color, fontfamily='sans-serif')

# Draw bubble legend manually in axes coords
ax2 = fig.add_axes([0.1, 0.01, 0.3, 0.05], facecolor='none')
ax2.set_xlim(0, 10)
ax2.set_ylim(0, 1)
ax2.axis('off')
for k, mem in enumerate(legend_mems):
    s = mem_to_size(mem)
    ax2.scatter(1 + k * 2.2, 0.5, s=s * 0.5, color=accent_color, alpha=0.4,
                edgecolors='white', linewidths=0.8)
    ax2.text(1 + k * 2.2, -0.3, f'{mem} MB', ha='center', fontsize=9,
             color=accent_color, fontfamily='sans-serif')
ax2.text(-0.5, 0.5, 'Size:', ha='right', va='center', fontsize=10,
         color=accent_color, fontfamily='sans-serif', fontweight='bold')

fig.subplots_adjust(left=0.1, right=0.96, top=0.89, bottom=0.13)

fig.savefig('benchmark-pareto.png', dpi=200,
            facecolor=bg_color, bbox_inches='tight', pad_inches=0.3)
print('Saved benchmark-pareto.png')
