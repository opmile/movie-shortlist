"""Experimento de calibração — varia o piso de count do Aclamado.

Lê etl/aggregated.csv (instantâneo, sem raw). Usa core.classify (precedência e
thresholds canônicos). Output é console — não emite artefato commitado.
Rode: python etl/explore/calibrate.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # etl/ on path → import core

import pandas as pd

from core import OUT_DIR, classify

ACLAMADO_FLOOR_CANDIDATES = [None, 6, 38, 100]


def main():
    df = pd.read_csv(OUT_DIR / "aggregated.csv")
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    order = ["Classico", "Cult", "Blockbuster", "Aclamado", "Filme"]
    print(f"Total filmes: {len(df):,}\n")
    print("piso".ljust(8) + "".join(c.ljust(13) for c in order))
    for floor in ACLAMADO_FLOOR_CANDIDATES:
        vc = classify(df, aclamado_floor=floor).value_counts().to_dict()
        label = "sem" if floor is None else str(floor)
        print(label.ljust(8) + "".join(f"{vc.get(c, 0):,}".ljust(13) for c in order))


if __name__ == "__main__":
    main()
