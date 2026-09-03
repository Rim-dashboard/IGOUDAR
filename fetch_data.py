"""
Génère data.json à partir de Yahoo Finance (yfinance), côté serveur.
Exécuté automatiquement toutes les heures par GitHub Actions (voir
.github/workflows/update-data.yml) — aucun problème de CORS puisque ce script
tourne sur un serveur, pas dans un navigateur.
"""
import json
import datetime as dt
import yfinance as yf

REF_DATE = dt.date(2025, 12, 25)

ASSETS = [
    "GOOGL", "NVDA", "MU", "WDC", "STX", "AVGO", "KLAC", "LRCX", "MSFT", "PLTR",
    "APP", "SNDK", "CLS", "TSM", "INTC",
    "CAT", "BWXT", "HWM", "GE",
    "ICLN", "TQQQ", "VTV", "AGG", "EEM", "SLVP", "GLD",
    "JPM", "BAC", "HOOD", "MS", "AXP", "V", "ALLY",
    "ISRG", "JNJ", "LLY", "VKTX", "DVAX", "OMER",
    "KGC", "SLV", "AA", "NEM", "SCCO", "FCX", "IAG", "CDE", "PAAS", "EQX", "AGI", "NEE", "FSLR",
]


def build():
    tickers = ASSETS + ["^GSPC"]
    raw = yf.download(
        tickers, start="2025-11-15", interval="1d",
        group_by="ticker", threads=True, progress=False, auto_adjust=True,
    )

    result = {}
    for ticker in tickers:
        try:
            df = raw[ticker][["Close"]].dropna()
        except Exception:
            continue
        if df.empty:
            continue
        df = df.copy()
        df.index = [d.date() if hasattr(d, "date") else d for d in df.index]

        ref_idx = min(df.index, key=lambda d: abs((d - REF_DATE).days))
        ref_price = float(df.loc[ref_idx, "Close"])
        last_price = float(df["Close"].iloc[-1])
        prev_price = float(df["Close"].iloc[-2]) if len(df) > 1 else last_price

        since_pct = (last_price / ref_price - 1) * 100 if ref_price else 0.0
        day_pct = (last_price / prev_price - 1) * 100 if prev_price else 0.0

        step = max(1, len(df) // 45)
        spark = [round(float(v), 4) for v in df["Close"].iloc[::step]]

        result[ticker] = {
            "price": round(last_price, 2),
            "prevClose": round(prev_price, 2),
            "since": round(since_pct, 2),
            "day": round(day_pct, 2),
            "spark": spark,
        }

    payload = {
        "generated_at": dt.datetime.utcnow().isoformat() + "Z",
        "reference_date": REF_DATE.isoformat(),
        "assets": result,
    }
    with open("data.json", "w") as f:
        json.dump(payload, f, separators=(",", ":"))

    print(f"data.json écrit avec {len(result)} instruments.")


if __name__ == "__main__":
    build()
