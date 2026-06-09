"""Regenera todos os snapshots do ETL, em ordem.

    python etl/build.py

Precisa de credenciais Kaggle + ~420MB de download (1ª vez; depois usa cache
local do kagglehub). Avaliadores NÃO precisam rodar isto — aggregated.csv e
neighbors.csv já vêm commitados. Ver etl/README.md.
"""
import time

import aggregate
import neighbors
import profile


def main():
    t0 = time.time()
    for name, stage in [("aggregate", aggregate), ("profile", profile), ("neighbors", neighbors)]:
        print(f"\n=== {name} ===")
        ts = time.time()
        stage.run()
        print(f"[{name}] {time.time() - ts:.1f}s")
    print(f"\n✓ build completo em {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
