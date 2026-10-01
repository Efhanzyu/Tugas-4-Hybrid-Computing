# KODE ASLI SLIDE 20 (belum diperbaiki) - dipakai hanya untuk mereproduksi error dan screenshot.
from mpi4py import MPI
from concurrent.futures import ProcessPoolExecutor
import numpy as np, time

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

def mc_pi(n_samples, seed):
    rng = np.random.default_rng(seed)
    x = rng.random(n_samples); y = rng.random(n_samples)
    inside = (x*x + y*y) <= 1.0
    return inside.sum()

def chunk_range(total, parts, idx):
    base = total // parts; rem = total % parts
    start = idx * base + min(idx, rem)
    end   = start + base + (1 if idx < rem else 0)
    return start, end

if __name__ == "__main__":
    TOTAL_TASKS = 8                 # misal 8 tugas per eksperimen
    SAMPLES_PER_TASK = 250_000      # 250k sampel per tugas
    start, end = chunk_range(TOTAL_TASKS, size, rank)
    my_tasks = range(start, end)

    t0 = time.time()
    with ProcessPoolExecutor(max_workers=4) as ex:
        hits = list(ex.map(lambda k: mc_pi(SAMPLES_PER_TASK, 1234 + rank*1000 + k),
                           my_tasks))
    local_hits = sum(hits)
    local_samples = len(my_tasks) * SAMPLES_PER_TASK
    t1 = time.time()

    # Reduce ke root: jumlah hits & sampel
    global_hits = comm.reduce(local_hits, op=MPI.SUM, root=0)
    global_samp = comm.reduce(local_samples, op=MPI.SUM, root=0)
    makespan = comm.reduce(t1 - t0, op=MPI.MAX, root=0)

    if rank == 0:
        pi_est = 4.0 * global_hits / global_samp
        print(f"[MPI ranks={size}] tasks={TOTAL_TASKS}, per_task={SAMPLES_PER_TASK}")
        print(f"Makespan     : {makespan:.3f} s")
        print(f"Total samples : {global_samp:,}")
        print(f"Estimasi pi   : {pi_est:.6f}")
