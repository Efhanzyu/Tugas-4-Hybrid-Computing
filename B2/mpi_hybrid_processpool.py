"""Hybrid MPI + ProcessPool (Monte Carlo pi) - VERSI PERBAIKAN.
Cara jalan:  mpiexec -n <ranks> python mpi_hybrid_processpool.py <workers>

Perubahan dari slide 20 (ditandai # UBAH):
 1. lambda diganti functools.partial (lambda tidak bisa di-pickle, jadi tidak bisa dikirim
    ke proses worker).
 2. 'from mpi4py import MPI' dipindah ke dalam main() (di dalam guard __main__). Di Windows,
    proses worker memakai 'spawn' dan meng-import ulang file ini; import mpi4py di level atas
    membuat setiap worker ikut menginisialisasi MPI (tidak seharusnya).
 3. mp_context = spawn dibuat eksplisit supaya perilaku sama di Windows/Linux.
 4. SAMPLES_PER_TASK = 200_000 + 10_000*A = 230_000 (A = 3).
 5. max_workers dibaca dari argumen command line (untuk grid otomatis).
"""
import sys, time
import multiprocessing as mp
from functools import partial                      # UBAH (1)
from concurrent.futures import ProcessPoolExecutor
import numpy as np


def mc_pi(n_samples, seed):
    rng = np.random.default_rng(seed)
    x = rng.random(n_samples)
    y = rng.random(n_samples)
    inside = (x * x + y * y) <= 1.0
    return int(inside.sum())


def chunk_range(total, parts, idx):
    base = total // parts
    rem = total % parts
    start = idx * base + min(idx, rem)
    end = start + base + (1 if idx < rem else 0)
    return start, end


def main():
    from mpi4py import MPI                         # UBAH (2): import di dalam main()
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    TOTAL_TASKS = 8
    SAMPLES_PER_TASK = 230_000                     # UBAH (4)
    N_WORKERS = int(sys.argv[1]) if len(sys.argv) > 1 else 4   # UBAH (5)

    start, end = chunk_range(TOTAL_TASKS, size, rank)
    my_tasks = range(start, end)
    seeds = [1234 + rank * 1000 + k for k in my_tasks]

    comm.Barrier()                                 # semua rank mulai bersamaan
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=N_WORKERS,
                             mp_context=mp.get_context("spawn")) as ex:   # UBAH (3)
        hits = list(ex.map(partial(mc_pi, SAMPLES_PER_TASK), seeds))      # UBAH (1)
    local_hits = sum(hits)
    local_samples = len(my_tasks) * SAMPLES_PER_TASK
    t1 = time.time()

    global_hits = comm.reduce(local_hits, op=MPI.SUM, root=0)
    global_samp = comm.reduce(local_samples, op=MPI.SUM, root=0)
    makespan = comm.reduce(t1 - t0, op=MPI.MAX, root=0)

    if rank == 0:
        pi_est = 4.0 * global_hits / global_samp
        print(f"[MPI ranks={size}] workers/rank={N_WORKERS} tasks={TOTAL_TASKS}, per_task={SAMPLES_PER_TASK}")
        print(f"Makespan     : {makespan:.3f} s")
        print(f"Total samples : {global_samp:,}")
        print(f"Estimasi pi   : {pi_est:.6f}")


if __name__ == "__main__":
    main()
