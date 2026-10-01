import csv
import re
import statistics
import subprocess
import sys
from pathlib import Path

REPEATS = 3
MPI_RANKS = 4
WORKERS_PER_RANK = 2

SCRIPT = Path(__file__).parent / "b3_global_word_count.py"
CSV_FILE = Path(__file__).parent / "b3_results.csv"

THREAD_PATTERN = re.compile(
    r"ThreadPoolExecutor\s*:\s*([\d.]+)\s*s"
)

PROCESS_PATTERN = re.compile(
    r"ProcessPoolExecutor:\s*([\d.]+)\s*s"
)


def run_once():
    cmd = [
        "mpiexec",
        "-n",
        str(MPI_RANKS),
        sys.executable,
        str(SCRIPT),
        str(WORKERS_PER_RANK),
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print("ERROR saat menjalankan B3")
        print(result.stdout)
        print(result.stderr)
        raise RuntimeError("Eksperimen B3 gagal.")

    thread_match = THREAD_PATTERN.search(result.stdout)
    process_match = PROCESS_PATTERN.search(result.stdout)

    if not thread_match or not process_match:
        print(result.stdout)
        raise RuntimeError(
            "Waktu ThreadPool/ProcessPool tidak ditemukan pada output."
        )

    thread_time = float(thread_match.group(1))
    process_time = float(process_match.group(1))

    return thread_time, process_time


def main():
    print("=" * 65)
    print("B3 - PERBANDINGAN THREADPOOL vs PROCESSPOOL")
    print("=" * 65)
    print(f"MPI rank            : {MPI_RANKS}")
    print(f"Worker per rank     : {WORKERS_PER_RANK}")
    print(f"Pengulangan         : {REPEATS}")
    print()

    rows = []

    for repeat in range(1, REPEATS + 1):
        print(f"Percobaan {repeat}/{REPEATS} ...")

        thread_time, process_time = run_once()

        print(f"  ThreadPool : {thread_time:.6f} s")
        print(f"  ProcessPool: {process_time:.6f} s")
        print()

        rows.append({
            "repeat": repeat,
            "threadpool_s": thread_time,
            "processpool_s": process_time,
        })

    thread_values = [row["threadpool_s"] for row in rows]
    process_values = [row["processpool_s"] for row in rows]

    thread_median = statistics.median(thread_values)
    process_median = statistics.median(process_values)

    # Simpan hasil percobaan dan median.
    with CSV_FILE.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.writer(f)

        writer.writerow([
            "repeat",
            "threadpool_s",
            "processpool_s",
        ])

        for row in rows:
            writer.writerow([
                row["repeat"],
                f'{row["threadpool_s"]:.6f}',
                f'{row["processpool_s"]:.6f}',
            ])

        writer.writerow([
            "median",
            f"{thread_median:.6f}",
            f"{process_median:.6f}",
        ])

    print("=" * 65)
    print("MEDIAN HASIL")
    print("=" * 65)
    print(f"ThreadPoolExecutor : {thread_median:.6f} s")
    print(f"ProcessPoolExecutor: {process_median:.6f} s")

    if thread_median < process_median:
        faster = "ThreadPoolExecutor"
        ratio = process_median / thread_median
    elif process_median < thread_median:
        faster = "ProcessPoolExecutor"
        ratio = thread_median / process_median
    else:
        faster = "Sama"
        ratio = 1.0

    print(f"Lebih cepat pada pengujian ini: {faster}")

    if faster != "Sama":
        print(f"Rasio waktu relatif: {ratio:.2f}x")

    print()
    print(f"Hasil tersimpan di: {CSV_FILE}")


if __name__ == "__main__":
    main()
