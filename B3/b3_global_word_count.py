from mpi4py import MPI
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from collections import Counter
from pathlib import Path
import multiprocessing as mp
import re
import sys
import time


# ============================================================
# KONFIGURASI
# ============================================================

STOPWORDS = {
    "dan",
    "yang",
    "di",
    "the",
    "of",
    "and",
}

TOKEN_PATTERN = re.compile(r"\b[\w'-]+\b", re.UNICODE)


# ============================================================
# WORKER FUNCTION
# Fungsi harus berada di level paling atas agar dapat
# dipanggil oleh ProcessPoolExecutor pada Windows.
# ============================================================

def count_words_in_file(file_path):
    """
    Membaca satu file teks dan menghitung frekuensi kata.
    """

    counter = Counter()

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read().lower()

    words = TOKEN_PATTERN.findall(text)

    for word in words:
        if word not in STOPWORDS:
            counter[word] += 1

    return counter


# ============================================================
# THREADPOOL VERSION
# ============================================================

def process_with_threads(files, workers):
    """
    Memproses file menggunakan ThreadPoolExecutor.
    """

    start = time.perf_counter()

    with ThreadPoolExecutor(max_workers=workers) as executor:
        counters = list(
            executor.map(count_words_in_file, files)
        )

    elapsed = time.perf_counter() - start

    total_counter = Counter()

    for counter in counters:
        total_counter.update(counter)

    return total_counter, elapsed


# ============================================================
# PROCESSPOOL VERSION
# ============================================================

def process_with_processes(files, workers):
    """
    Memproses file menggunakan ProcessPoolExecutor.

    Pada Windows digunakan multiprocessing context 'spawn'
    agar kompatibel dengan sistem operasi Windows.
    """

    start = time.perf_counter()

    context = mp.get_context("spawn")

    with ProcessPoolExecutor(
        max_workers=workers,
        mp_context=context
    ) as executor:

        counters = list(
            executor.map(count_words_in_file, files)
        )

    elapsed = time.perf_counter() - start

    total_counter = Counter()

    for counter in counters:
        total_counter.update(counter)

    return total_counter, elapsed


# ============================================================
# MAIN
# ============================================================

def main():

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    # --------------------------------------------------------
    # Argumen
    # python b3_global_word_count.py [workers]
    # --------------------------------------------------------

    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 2

    dataset_dir = Path(__file__).parent / "dataset"

    if rank == 0:

        files = sorted(dataset_dir.glob("*.txt"))

        print("=" * 60)
        print("B3 - GLOBAL WORD COUNT")
        print("=" * 60)

        print(f"Jumlah MPI rank : {size}")
        print(f"Worker per rank : {workers}")
        print(f"Jumlah file     : {len(files)}")

        if len(files) < 30:
            print()
            print("PERINGATAN:")
            print("Dataset harus memiliki minimal 30 file teks.")
            print("=" * 60)

    else:
        files = None

    # Broadcast daftar file ke seluruh rank
    files = comm.bcast(files, root=0)

    if len(files) < 30:
        return

    # --------------------------------------------------------
    # Pembagian file antar MPI rank
    # --------------------------------------------------------

    local_files = files[rank::size]

    print(
        f"[Rank {rank}] mendapatkan {len(local_files)} file",
        flush=True
    )

    # ========================================================
    # VERSION 1 - THREADPOOL
    # ========================================================

    comm.Barrier()

    thread_counter, thread_time = process_with_threads(
        local_files,
        workers
    )

    # Ambil waktu terlama dari seluruh rank
    max_thread_time = comm.reduce(
        thread_time,
        op=MPI.MAX,
        root=0
    )

    # Gabungkan Counter seluruh rank
    thread_counters = comm.gather(
        thread_counter,
        root=0
    )

    # ========================================================
    # VERSION 2 - PROCESSPOOL
    # ========================================================

    comm.Barrier()

    process_counter, process_time = process_with_processes(
        local_files,
        workers
    )

    # Ambil waktu terlama dari seluruh rank
    max_process_time = comm.reduce(
        process_time,
        op=MPI.MAX,
        root=0
    )

    # Gabungkan Counter seluruh rank
    process_counters = comm.gather(
        process_counter,
        root=0
    )

    # ========================================================
    # HASIL GLOBAL
    # ========================================================

    if rank == 0:

        global_thread_counter = Counter()

        for counter in thread_counters:
            global_thread_counter.update(counter)

        global_process_counter = Counter()

        for counter in process_counters:
            global_process_counter.update(counter)

        print()
        print("=" * 60)
        print("HASIL EKSPERIMEN")
        print("=" * 60)

        print(f"ThreadPoolExecutor : {max_thread_time:.6f} s")
        print(f"ProcessPoolExecutor: {max_process_time:.6f} s")

        print()
        print("Top 10 kata - ThreadPoolExecutor")
        print("-" * 40)

        for word, count in global_thread_counter.most_common(10):
            print(f"{word:20s} {count}")

        print()
        print("Top 10 kata - ProcessPoolExecutor")
        print("-" * 40)

        for word, count in global_process_counter.most_common(10):
            print(f"{word:20s} {count}")

        print()
        print("=" * 60)

        if max_thread_time < max_process_time:
            print("ThreadPoolExecutor lebih cepat pada eksperimen ini.")
        elif max_process_time < max_thread_time:
            print("ProcessPoolExecutor lebih cepat pada eksperimen ini.")
        else:
            print("Kedua metode memiliki waktu yang sama.")

        print("=" * 60)


if __name__ == "__main__":
    main()
