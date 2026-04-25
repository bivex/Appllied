#!/usr/bin/env python3
"""Benchmark PDF extraction performance improvements."""

import time
import subprocess
import sys
from pathlib import Path


def benchmark(args, repeats=3):
    """Run extraction multiple times and return avg time."""
    times = []
    for i in range(repeats):
        start = time.time()
        result = subprocess.run(
            [sys.executable, "-m", "ocr_system.scripts.extract_text_from_pdf"] + args,
            capture_output=True,
            text=True,
        )
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"  Run {i + 1}: {elapsed:.2f}s")
    avg = sum(times) / len(times)
    return avg, times


if __name__ == "__main__":
    pdf = "test/Русския_сказки_для_детей_разсказанныя_нянюшкою_Авдотьею_Степановною.pdf"
    if not Path(pdf).exists():
        print(f"PDF not found: {pdf}")
        sys.exit(1)

    print("=" * 60)
    print("PDF Extraction Benchmark")
    print(f"Document: {pdf}")
    print("=" * 60)

    # Test different configurations
    configs = [
        (
            "Sequential, scale 1.5, pages 1-10",
            ["--pages", "1-10", "--scale", "1.5", "--jobs", "1"],
        ),
        (
            "Parallel 4 workers, scale 1.5, pages 1-10",
            ["--pages", "1-10", "--scale", "1.5", "--jobs", "4"],
        ),
        (
            "Parallel 8 workers, scale 1.5, pages 1-10",
            ["--pages", "1-10", "--scale", "1.5", "--jobs", "8"],
        ),
    ]

    results = []
    for name, extra_args in configs:
        print(f"\n{name}:")
        avg, times = benchmark([pdf] + extra_args, repeats=2)
        results.append((name, avg))
        print(f"  Average: {avg:.2f}s")

    print("\n" + "=" * 60)
    print("Summary:")
    for name, avg in results:
        print(f"  {name}: {avg:.2f}s")

    if len(results) >= 2:
        speedup = results[0][1] / results[1][1]
        print(f"\nSpeedup (parallel vs sequential): {speedup:.2f}x")
