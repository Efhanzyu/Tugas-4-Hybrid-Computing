import os, random, string, pathlib, sys

A = 3                       # digit terakhir NPM 247006111183
N_FILES = 100 + 10 * A      # = 130
pathlib.Path("data").mkdir(exist_ok=True)
random.seed(42)             # supaya dataset bisa direproduksi
for i in range(1, N_FILES + 1):
    s = "".join(random.choice(string.ascii_letters + " " * 5 + "\n") for _ in range(3000))
    with open(f"data/file_{i:03d}.txt", "w") as f:
        f.write(s)
print(f"done. {N_FILES} file dibuat di ./data")
