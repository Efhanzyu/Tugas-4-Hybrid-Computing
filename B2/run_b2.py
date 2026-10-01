"""Grid B2: ranks {1,2,4} x workers {1,2,4} -> b2_results.csv (+ b2_speedup.png).
Tiap kombinasi diulang REPEATS kali, diambil median makespan.
Speedup S = T1 / Tn  (T1 = konfigurasi 1 rank x 1 worker)
Efisiensi E = S / n   dengan n = ranks x workers (total unit paralel)."""
import csv, os, re, statistics, subprocess, sys

RANKS = [1, 2, 4]
WORKERS = [1, 2, 4]
REPEATS = 3
EXTRA = os.environ.get("MPIEXEC_EXTRA", "").split()     # mis. --oversubscribe di Linux
PAT = re.compile(r"Makespan\s*:\s*([\d.]+)")


def run_once(r, w):
    cmd = ["mpiexec", *EXTRA, "-n", str(r), sys.executable, "mpi_hybrid_processpool.py", str(w)]
    out = subprocess.run(cmd, capture_output=True, text=True)
    m = PAT.search(out.stdout)
    if not m:
        raise RuntimeError(f"Gagal parse output:\n{out.stdout}\n{out.stderr}")
    return float(m.group(1))


if __name__ == "__main__":
    run_once(1, 1)                                   # warm-up
    rows = []
    for r in RANKS:
        for w in WORKERS:
            t = statistics.median(run_once(r, w) for _ in range(REPEATS))
            rows.append({"ranks": r, "workers": w, "n": r * w, "makespan_s": round(t, 3)})
            print(rows[-1])
    t1 = next(x["makespan_s"] for x in rows if x["ranks"] == 1 and x["workers"] == 1)
    for x in rows:
        x["speedup"] = round(t1 / x["makespan_s"], 2)
        x["efficiency"] = round(x["speedup"] / x["n"], 2)

    with open("b2_results.csv", "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=rows[0].keys())
        wr.writeheader()
        wr.writerows(rows)
    print("\nranks workers  n  makespan  speedup  efficiency")
    for x in rows:
        print(f"{x['ranks']:>5} {x['workers']:>7} {x['n']:>2} {x['makespan_s']:>8} {x['speedup']:>8} {x['efficiency']:>10}")
    print("Tersimpan: b2_results.csv")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(6, 4))
        for r in RANKS:
            ax.plot(WORKERS, [x["speedup"] for x in rows if x["ranks"] == r], marker="o", label=f"{r} rank MPI")
        ax.set_xlabel("max_workers per rank"); ax.set_ylabel("Speedup (T1 / Tn)")
        ax.set_xticks(WORKERS); ax.grid(alpha=.3); ax.legend()
        plt.tight_layout(); plt.savefig("b2_speedup.png", dpi=150)
        print("Tersimpan: b2_speedup.png")
    except ImportError:
        print("matplotlib belum terpasang")
