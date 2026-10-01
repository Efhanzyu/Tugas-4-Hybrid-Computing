
import os, time, threading, queue, string
from concurrent.futures import ProcessPoolExecutor, as_completed

DATA_DIR = "./data"


def cpu_task(path):
    t0 = time.time()
    with open(path, "rb") as f:
        data = f.read()
    text = data.decode(errors="ignore").lower()
    alpha = sum(c in string.ascii_lowercase for c in text)
    latency = time.time() - t0
    return {"path": path, "alpha": alpha, "latency": latency}


def loader_worker(q, files):
    for p in files:
        q.put(p)          # blok jika antrian penuh (backpressure)
    q.put(None)           # sentinel: loader ini selesai


# UBAH: n_threads, n_workers, q_max jadi argumen (di slide: konstanta global)
def run_pipeline(n_threads=2, n_workers=4, q_max=32, verbose=True):
    files = [os.path.join(DATA_DIR, f) for f in os.listdir(DATA_DIR)
             if os.path.isfile(os.path.join(DATA_DIR, f))]
    if not files:
        raise SystemExit("Folder ./data kosong - jalankan gen_data.py dulu.")

    chunks = [files[i::n_threads] for i in range(n_threads)]
    q = queue.Queue(maxsize=q_max)

    loaders = []
    for ch in chunks:
        t = threading.Thread(target=loader_worker, args=(q, ch), daemon=True)
        loaders.append(t)
        t.start()

    done = 0
    results, lat = [], []
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=n_workers) as ex:
        futs = set()
        while done < n_threads:
            item = q.get()
            if item is None:
                done += 1
                continue
            futs.add(ex.submit(cpu_task, item))
        for fut in as_completed(futs):
            r = fut.result()
            results.append(r)
            lat.append(r["latency"])

    total = time.time() - t0
    thr = len(results) / total if total > 0 else 0.0
    avg_lat = sum(lat) / len(lat) if lat else 0.0

    if verbose:
        print(f"Files      : {len(results)}")
        print(f"Threads (I/O) : {n_threads} | Processes (CPU): {n_workers} | Q_MAX: {q_max}")
        print(f"Total time : {total:.3f} s")
        print(f"Throughput : {thr:.2f} files/s")
        print(f"Avg latency: {avg_lat:.4f} s/file")

    # UBAH: kembalikan hasil sebagai dict
    return {"files": len(results), "total": total, "throughput": thr, "avg_latency": avg_lat}


if __name__ == "__main__":
    run_pipeline()

