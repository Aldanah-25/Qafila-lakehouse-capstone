
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent

def execute(label, command):
    print(f"\n=== {label} ===", flush=True)
    result = subprocess.run(
        command,
        cwd=str(PROJECT)
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"{label} failed: exit {result.returncode}"
        )

def main():
    execute(
        "SDAIA Dagster + dbt pipeline",
        [sys.executable, "capstone/pipeline.py"]
    )

    execute(
        "Quality and incremental extension",
        [sys.executable, "quality_pipeline.py"]
    )

    print("\nQAFILA PIPELINE COMPLETED SUCCESSFULLY")

if __name__ == "__main__":
    main()
