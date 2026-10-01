import csv, statistics
from hybrid_pipeline import run_pipeline

THREADS = [1, 2, 4]
WORKERS = [1, 2, 4, 8]      # 8 = jumlah core fisik i5-12450H
QMAX = [4, 32]
REPEATS = 3

if __name__ == "__main__":      # wajib di Windows (multiprocessing memakai spawn)
    run_pipeline(2, 4, 32, verbose=False)   # warm-up, tidak dicatat
    rows = []
    for q in QMAX:
        for t in THREADS:
            for w in WORKERS:
                runs = [run_pipeline(t, w, q, verbose=False) for _ in range(REPEATS)]
                row = {
                    "Q_MAX": q, "threads": t, "workers": w,
                    "total_s": round(statistics.median(r["total"] for r in runs), 3),
                    "throughput": round(statistics.median(r["throughput"] for r in runs), 2),
                    "avg_latency_s": round(statistics.median(r["avg_latency"] for r in runs), 4),
                }
                rows.append(row)
                print(row)

    with open("b1_results.csv", "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=rows[0].keys())
        wr.writeheader()
        wr.writerows(rows)
    print("Tersimpan: b1_results.csv")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
        for ax, q in zip(axes, QMAX):
            for t in THREADS:
                ys = [r["throughput"] for r in rows if r["Q_MAX"] == q and r["threads"] == t]
                ax.plot(WORKERS, ys, marker="o", label=f"{t} thread I/O")
            ax.set_title(f"Q_MAX = {q}")
            ax.set_xlabel("N_WORKERS (proses CPU)")
            ax.set_xticks(WORKERS)
            ax.grid(alpha=.3)
        axes[0].set_ylabel("Throughput (file/s)")
        axes[1].legend()
        plt.tight_layout()
        plt.savefig("b1_throughput.png", dpi=150)
        print("Tersimpan: b1_throughput.png")
    except ImportError:
        print("matplotlib belum terpasang: python -m pip install matplotlib")
