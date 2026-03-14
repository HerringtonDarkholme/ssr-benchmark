#!/usr/bin/env python3
"""Generate a radar chart comparing AST tools across 6 dimensions."""
import matplotlib.pyplot as plt
import numpy as np

# ── Data ─────────────────────────────────────────────────────────
tools = ['ast-grep', 'GritQL', 'recast', 'jscodeshift', 'semgrep']
colors = ['#3b82f6', '#22c55e', '#a855f7', '#f59e0b', '#ef4444']
fill_alphas = [0.25, 0.12, 0.12, 0.12, 0.12]

# Raw values (lower = better for all)
raw = {
    'Search Speed':          [43, 80, 200, 754, 7535],
    'Transform Speed':       [41, 816, 200, 808, 13111],
    'Complex Search Speed':  [44, 1486, 199, 764, 1433],
    'Search Memory':         [11, 58, 93, 153, 250],
    'Transform Memory':      [10, 57, 95, 157, 327],
    'Complex Search Memory': [11, 58, 95, 154, 231],
}

dimensions = list(raw.keys())
n_dims = len(dimensions)

# Normalize: invert so that higher = better, scale 0-1
# Use log scale for speed dimensions to avoid one tool dominating
normalized = {}
for dim in dimensions:
    vals = np.array(raw[dim], dtype=float)
    log_vals = np.log10(vals)
    worst = log_vals.max()
    best = log_vals.min()
    if worst == best:
        normalized[dim] = [1.0] * len(vals)
    else:
        # Invert: best (lowest) gets 1.0, worst (highest) gets ~0.1
        normalized[dim] = [0.1 + 0.9 * (worst - v) / (worst - best) for v in log_vals]

# ── Style ─────────────────────────────────────────────────────────
bg_color = '#0f172a'
card_color = '#1e293b'
text_color = '#e2e8f0'
grid_color = '#475569'
accent_color = '#94a3b8'

fig = plt.figure(figsize=(10, 10), facecolor=bg_color)
ax = fig.add_subplot(111, polar=True, facecolor=card_color)

# ── Radar angles ─────────────────────────────────────────────────
angles = np.linspace(0, 2 * np.pi, n_dims, endpoint=False).tolist()
angles += angles[:1]  # close the polygon

# ── Plot each tool ───────────────────────────────────────────────
for i, tool in enumerate(tools):
    values = [normalized[dim][i] for dim in dimensions]
    values += values[:1]  # close

    ax.plot(angles, values, color=colors[i], linewidth=2.5,
            linestyle='-', label=tool, zorder=3 + i)
    ax.fill(angles, values, color=colors[i], alpha=fill_alphas[i], zorder=2 + i)

    # Mark vertices
    ax.scatter(angles[:-1], values[:-1], color=colors[i], s=50,
               edgecolors='white', linewidths=1, zorder=5 + i)

# ── Axis labels ──────────────────────────────────────────────────
# Shorter labels for readability
short_labels = [
    'Search\nSpeed',
    'Transform\nSpeed',
    'Complex Search\nSpeed',
    'Search\nMemory',
    'Transform\nMemory',
    'Complex Search\nMemory',
]

ax.set_xticks(angles[:-1])
ax.set_xticklabels(short_labels, fontsize=12, color=text_color,
                   fontfamily='sans-serif', fontweight='bold')

# Adjust label padding
ax.tick_params(axis='x', pad=18)

# ── Grid styling ─────────────────────────────────────────────────
ax.set_ylim(0, 1.05)
ax.set_yticks([0.25, 0.5, 0.75, 1.0])
ax.set_yticklabels(['', '', '', ''], color=accent_color)
ax.yaxis.grid(True, color=grid_color, linewidth=0.5, alpha=0.6)
ax.xaxis.grid(True, color=grid_color, linewidth=0.5, alpha=0.6)

# Spines
ax.spines['polar'].set_color(grid_color)
ax.spines['polar'].set_linewidth(0.5)

# ── Ring labels (inside) ─────────────────────────────────────────
for val, label in [(0.25, 'Poor'), (0.5, ''), (0.75, 'Good'), (1.0, 'Best')]:
    ax.text(np.pi / n_dims, val + 0.02, label, fontsize=9, color=accent_color,
            fontfamily='sans-serif', ha='center', va='bottom', alpha=0.7)

# ── Legend ────────────────────────────────────────────────────────
leg = ax.legend(loc='upper right', bbox_to_anchor=(1.28, 1.1),
                fontsize=13, frameon=True, facecolor=card_color,
                edgecolor=grid_color, labelcolor=text_color,
                borderpad=1, handlelength=2, handletextpad=0.8)

# ── Title ────────────────────────────────────────────────────────
fig.text(0.5, 0.97, 'AST Tool Benchmark', ha='center', va='top',
         fontsize=26, fontweight='bold', color=text_color,
         fontfamily='sans-serif')
fig.text(0.5, 0.935, 'Higher = faster speed & lower memory. 6 dimensions, log-normalized.',
         ha='center', va='top', fontsize=13, color=accent_color,
         fontfamily='sans-serif')

fig.subplots_adjust(left=0.08, right=0.78, top=0.88, bottom=0.05)

fig.savefig('benchmark-pareto.png', dpi=200,
            facecolor=bg_color, bbox_inches='tight', pad_inches=0.5)
print('Saved benchmark-pareto.png')
