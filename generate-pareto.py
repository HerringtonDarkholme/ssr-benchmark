#!/usr/bin/env python3
"""Generate a Pareto-front style scatter plot of time vs memory."""
import matplotlib.pyplot as plt
import numpy as np

# ── Data: (time_ms, memory_mb) per task per tool ─────────────────
tools = ['ast-grep', 'GritQL', 'recast', 'jscodeshift', 'semgrep']
colors = ['#3b82f6', '#22c55e', '#a855f7', '#f59e0b', '#ef4444']
markers = ['o', 's', 'D', '^', 'v']

# Each tool has 3 data points: (time, memory) for each task
data = {
    'ast-grep':    [(43, 11),  (41, 10),  (44, 11)],
    'GritQL':      [(80, 58),  (816, 57), (1486, 58)],
    'recast':      [(199, 93), (200, 95), (199, 95)],
    'jscodeshift': [(754, 153),(808, 157),(764, 154)],
    'semgrep':     [(7535,250),(13111,327),(1433,231)],
}

task_labels = ['Search', 'Transform', 'Complex Search']

# ── Style ─────────────────────────────────────────────────────────
bg_color = '#0f172a'
card_color = '#1e293b'
text_color = '#e2e8f0'
grid_color = '#334155'
accent_color = '#94a3b8'

fig, ax = plt.subplots(figsize=(12, 8), facecolor=bg_color)
ax.set_facecolor(card_color)

# ── Plot each tool ───────────────────────────────────────────────
for i, tool in enumerate(tools):
    pts = data[tool]
    times = [p[0] for p in pts]
    mems = [p[1] for p in pts]

    # Sort points by time for clean line connection
    order = np.argsort(times)
    times_sorted = [times[j] for j in order]
    mems_sorted = [mems[j] for j in order]

    # Dashed line connecting the 3 task results
    ax.plot(times_sorted, mems_sorted, color=colors[i], linestyle='--',
            linewidth=1.8, alpha=0.6, zorder=2)

    # Points for each task
    for j, (t, m) in enumerate(pts):
        ax.scatter(t, m, color=colors[i], s=120, marker=markers[i],
                   edgecolors='white', linewidths=1.2, zorder=4)

    # Label: place near the median point
    median_idx = order[1]
    label_t = times[median_idx]
    label_m = mems[median_idx]

    # Offset labels to avoid overlap
    offsets = {
        'ast-grep': (-8, -18),
        'GritQL': (12, -16),
        'recast': (12, -4),
        'jscodeshift': (12, -4),
        'semgrep': (-20, -20),
    }
    ox, oy = offsets[tool]
    ax.annotate(tool, (label_t, label_m), textcoords='offset points',
                xytext=(ox, oy), fontsize=13, fontweight='bold',
                color=colors[i], fontfamily='sans-serif', zorder=5)

# ── "Better" corner annotation ───────────────────────────────────
# Arrow pointing toward top-left (fast + low memory)
ax.annotate('', xy=(28, 5), xytext=(90, 40),
            arrowprops=dict(arrowstyle='->', color='#22c55e',
                            lw=2.5, connectionstyle='arc3,rad=0'))
ax.text(30, 42, 'Better', fontsize=14, fontweight='bold',
        color='#22c55e', fontfamily='sans-serif', fontstyle='italic')

# ── Axes ─────────────────────────────────────────────────────────
ax.set_xscale('log')
ax.set_yscale('log')

ax.invert_xaxis()
ax.invert_yaxis()

ax.set_xlabel('Time (ms) — faster →', fontsize=14, color=text_color,
              fontfamily='sans-serif', labelpad=10)
ax.set_ylabel('Memory (MB) — lighter →', fontsize=14, color=text_color,
              fontfamily='sans-serif', labelpad=10)

ax.tick_params(axis='both', colors=accent_color, labelsize=11)

import matplotlib.ticker as ticker
ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{int(x):,}'))
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{int(x)}'))

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_color(grid_color)
ax.spines['left'].set_color(grid_color)
ax.grid(True, color=grid_color, linewidth=0.5, alpha=0.5, zorder=0)

# ── Task shape legend ────────────────────────────────────────────
task_markers = ['o', 'o', 'o']
legend_elements = []
for j, label in enumerate(task_labels):
    legend_elements.append(
        plt.scatter([], [], marker=['o', 's', 'D'][j], s=80,
                    color=accent_color, edgecolors='white', linewidths=0.8,
                    label=label)
    )

leg = ax.legend(handles=legend_elements, loc='lower left', fontsize=11,
                frameon=True, facecolor=card_color, edgecolor=grid_color,
                labelcolor=text_color, borderpad=0.8, handletextpad=0.6)

# Actually, since all tools use their own marker, let's use a simpler approach:
# Show task markers in a separate annotation
ax.legend().remove()

# Task marker legend (bottom-left)
for j, (label, mk) in enumerate(zip(task_labels, ['o', 's', 'D'])):
    y_base = 0.08
    ax.text(0.03, y_base + j * 0.045, f'  {label}', transform=ax.transAxes,
            fontsize=11, color=text_color, fontfamily='sans-serif', va='center')
    ax.plot(0.02, y_base + j * 0.045, marker=mk, transform=ax.transAxes,
            color=accent_color, markersize=8, markeredgecolor='white',
            markeredgewidth=0.8, linestyle='none', clip_on=False)

# ── Title ────────────────────────────────────────────────────────
ax.set_title('Speed vs Memory: Pareto View\n',
             fontsize=20, fontweight='bold', color=text_color,
             fontfamily='sans-serif', pad=15)
fig.text(0.5, 0.92, 'Each point is one task. Closer to top-right is better.',
         ha='center', fontsize=12, color=accent_color, fontfamily='sans-serif')

# Redraw points with per-task markers
while ax.collections:
    ax.collections[0].remove()
for i, tool in enumerate(tools):
    pts = data[tool]
    for j, (t, m) in enumerate(pts):
        mk = ['o', 's', 'D'][j]
        ax.scatter(t, m, color=colors[i], s=120, marker=mk,
                   edgecolors='white', linewidths=1.2, zorder=4)

fig.savefig('benchmark-pareto.png', dpi=200,
            facecolor=bg_color, bbox_inches='tight', pad_inches=0.3)
print('Saved benchmark-pareto.png')
