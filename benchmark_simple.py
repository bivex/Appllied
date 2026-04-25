#!/usr/bin/env python3
"""Quick benchmark script comparing sequential vs parallel extraction."""

import time
import subprocess
import sys
from pathlib import Path


def timed_run(args):
    start = time.time()
    result = subprocess.run(
        [sys.executable, "-m", "ocr_system.scripts.extract_text_from_pdf"] + args,
        capture_output=True,
        text=True,
    )
    elapsed = time.time() - start
    return elapsed, result.returncode == 0


if __name__ == "__main__":
    pdf = "test/Русския_сказки_для_детей_разсказанныя_нянюшкою_Авдотьею_Степановною.pdf"
    base_args = [pdf, "--pages", "1-20", "--scale", "1.5", "--output", "/dev/null"]

    print("Sequential (jobs=1):")
    t1, ok1 = timed_run(base_args + ["--jobs", "1"])
    print(f"  {t1:.2f}s")

    print("\nParallel (jobs=4):")
    t4, ok4 = timed_run(base_args + ["--jobs", "4"])
    print(f"  {t4:.2f}s")

    if ok1 and ok4:
        speedup = t1 / t4
        print(f"\nSpeedup: {speedup:.2f}x")
        print(f"Time saved: {t1 - t4:.2f}s ({(1 - t4 / t1) * 100:.0f}%)")
    else:
        print("\nSome runs failed!")
