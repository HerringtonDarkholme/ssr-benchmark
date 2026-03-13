#!/usr/bin/env python3
"""Reads results.csv and prints a summary table with median times and memory."""
import csv
import sys
from collections import defaultdict
from statistics import median

def main():
    csvfile = sys.argv[1]
    data = defaultdict(lambda: defaultdict(lambda: {"real": [], "rss": []}))

    with open(csvfile) as f:
        reader = csv.DictReader(f)
        for row in reader:
            tool = row["tool"]
            task = row["task"]
            data[task][tool]["real"].append(int(row["real_ms"]))
            data[task][tool]["rss"].append(int(row["max_rss_kb"]))

    tasks = list(data.keys())
    all_tools = sorted({t for task in data.values() for t in task})

    # Header
    print(f"\n{'Task':<28} ", end="")
    for tool in all_tools:
        print(f"| {tool:<18} ", end="")
    print("|")
    print("-" * 30, end="")
    for _ in all_tools:
        print("+" + "-" * 20, end="")
    print("+")

    for task in tasks:
        # Time row
        print(f"{task:<28} ", end="")
        times = {}
        for tool in all_tools:
            if tool in data[task]:
                med = median(data[task][tool]["real"])
                times[tool] = med
            else:
                times[tool] = None

        best = min((v for v in times.values() if v is not None), default=0)
        for tool in all_tools:
            v = times[tool]
            if v is None:
                print(f"| {'N/A':>14} ms  ", end="")
            else:
                marker = " *" if v == best else "  "
                print(f"| {v:>10.0f} ms{marker}  ", end="")
        print("|")

        # Memory row
        print(f"{'  (peak RSS MB)':<28} ", end="")
        for tool in all_tools:
            if tool in data[task]:
                rss_mb = median(data[task][tool]["rss"]) / 1024
                print(f"| {rss_mb:>10.1f} MB    ", end="")
            else:
                print(f"| {'N/A':>14} MB  ", end="")
        print("|")

    print()
    print("* = fastest for that task")
    print()

if __name__ == "__main__":
    main()
