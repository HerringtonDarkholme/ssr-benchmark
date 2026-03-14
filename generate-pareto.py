#!/usr/bin/env python3
"""Generate a bubble chart: x=time, y=tool, bubble size=memory, faceted by task."""
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# ── Data ─────────────────────────────────────────────────────────
tools = ['ast-grep', 'GritQL', 'recast', 'jscodeshift', 'semgrep']
colors = ['#3b82f6', '#22c55e', '#a855f7', '#f59e0b', '#ef4444']

tasks = ['Search console.log', 'Transform var → const', 'Search async + try/catch']

# (time_ms, memory_mb) per tool per task
data = {
    'Search console.log':         [(43,11), (80,58), (200,93), (754,153), (7535,250)],
    'Transform var → const':      [(41,10), (816,57), (200,95), (808,157), (13111,327)],
    'Search async + try/catch':   [(44,11), (1486,58), (199,95), (764,154), (1433,231)],
}

# ── Style ─────────────────────────────────────────────────────────
bg_color = '#0f172a'
card_color = '#1e293b'
text_color = '#e2e8f0'
grid_color = '#334155'
accent_color = '#94a3b8'

fig, axes = plt.subplots(3, 1, figsize=(14, 10), facecolor=bg_color,
                         gridspec_kw={'hspace': 0.55})

fig.text(0.5, 0.97, 'AST Tool Benchmark: Speed & Memory', ha='center', va='top',
         fontsize=24, fontweight='bold', color=text_color, fontfamily='sans-serif')
fig.text(0.5, 0.935, 'Bubble size = peak memory usage. Further left = faster.',
         ha='center', va='top', fontsize=13, color=accent_color, fontfamily='sans-serif')

# Scale factor: map memory MB to bubble point size
# We want 10MB → small dot, 327MB → big circle
def mem_to_size(mb):
    return (mb / 327) * 2200 + 80

n_tools = len(tools)

for ax_idx, task in enumerate(tasks):
    ax = axes[ax_idx]
    ax.set_facecolor(card_color)

    y_pos = np.arange(n_tools)
    pts = data[task]

    for i, (t, m) in enumerate(pts):
        s = mem_to_size(m)
        ax.scatter(t, i, s=s, color=colors[i], alpha=0.75,
                   edgecolors='white', linewidths=1.5, zorder=4)

        # Label: time and memory to the right of the bubble
        bubble_radius_approx = np.sqrt(s / np.pi) * 0.8
        ax.annotate(f'{t:,}ms  ({m} MB)',
                    xy=(t, i), xytext=(bubble_radius_approx + 8, 0),
                    textcoords='offset points', fontsize=11,
                    fontweight='bold', color=colors[i],
                    fontfamily='sans-serif', va='center', zorder=5)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(tools, fontsize=13, fontweight='bold',
                       color=text_color, fontfamily='sans-serif')
    ax.set_ylim(-0.6, n_tools - 0.4)
    ax.invert_yaxis()

    ax.set_xscale('log')
    ax.set_xlim(20, 25000)
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{int(x):,}'))
    ax.tick_params(axis='x', colors=accent_color, labelsize=10)
    ax.tick_params(axis='y', length=0)

    ax.set_xlabel('Time (ms, log scale)', fontsize=10, color=accent_color,
                  fontfamily='sans-serif')

    ax.set_title(task, fontsize=15, fontweight='bold', color=text_color,
                 fontfamily='sans-serif', pad=10, loc='left')

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color(grid_color)
    ax.spines['left'].set_visible(False)
    ax.grid(axis='x', color=grid_color, linewidth=0.5, alpha=0.5, zorder=0)

# ── Bubble size legend (in bottom-right of last axes) ────────────
ax_last = axes[-1]
legend_mems = [10, 100, 300]
legend_y_positions = [3.6, 3.9, 4.25]
for mem, ly in zip(legend_mems, legend_y_positions):
    s = mem_to_size(mem)
    ax_last.scatter(15000, ly, s=s * 0.4, color=accent_color, alpha=0.35,
                    edgecolors='white', linewidths=1, zorder=1, clip_on=False)
    ax_last.text(18500, ly, f'{mem} MB', fontsize=9, color=accent_color,
                 fontfamily='sans-serif', va='center', clip_on=False)

fig.text(0.5, 0.005, 'Bubble size = peak memory usage  ·  Further left & smaller = better',
         ha='center', fontsize=12, color=accent_color, fontfamily='sans-serif')

fig.savefig('benchmark-pareto.png', dpi=200,
            facecolor=bg_color, bbox_inches='tight', pad_inches=0.4)
print('Saved benchmark-pareto.png')
