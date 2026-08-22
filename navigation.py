from __future__ import annotations

import argparse
import csv
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Position:
    x: float = 0.0
    y: float = 0.0


def truth_velocity(t: float) -> tuple[float, float]:
    speed = 55.0 + 3.0 * math.sin(t / 7.0)
    heading = math.radians(20.0 + 0.45 * t)
    return speed * math.cos(heading), speed * math.sin(heading)


def simulate(duration: float, outage_start: float, outage_end: float, seed: int = 11, dt: float = 0.2) -> list[dict[str, float | str]]:
    rng = random.Random(seed); truth = Position(); est = Position(); rows = []
    for i in range(int(duration / dt) + 1):
        t = i * dt; vx, vy = truth_velocity(t)
        truth.x += vx * dt; truth.y += vy * dt
        measured_vx = vx + rng.gauss(0, 0.8); measured_vy = vy + rng.gauss(0, 0.8)
        est.x += measured_vx * dt; est.y += measured_vy * dt
        source = "dead_reckoning"
        gps_available = not (outage_start <= t <= outage_end)
        if gps_available and i % int(1.0 / dt) == 0:
            est.x = 0.25 * est.x + 0.75 * (truth.x + rng.gauss(0, 2.0))
            est.y = 0.25 * est.y + 0.75 * (truth.y + rng.gauss(0, 2.0)); source = "gps"
        elif not gps_available and i % int(8.0 / dt) == 0 and t > outage_start:
            est.x = 0.6 * est.x + 0.4 * (truth.x + rng.gauss(0, 6.0))
            est.y = 0.6 * est.y + 0.4 * (truth.y + rng.gauss(0, 6.0)); source = "landmark"
        error = math.hypot(est.x - truth.x, est.y - truth.y)
        rows.append({"t_s": t, "truth_x_m": truth.x, "truth_y_m": truth.y,
                     "estimated_x_m": est.x, "estimated_y_m": est.y, "position_error_m": error,
                     "update_source": source})
    return rows


def metrics(rows: list[dict[str, float | str]]) -> dict[str, float | int]:
    errors = [float(r["position_error_m"]) for r in rows]
    return {"samples": len(rows), "max_position_error_m": round(max(errors), 2),
            "rms_position_error_m": round(math.sqrt(sum(e*e for e in errors)/len(errors)), 2),
            "landmark_updates": sum(r["update_source"] == "landmark" for r in rows)}


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--duration", type=float, default=60)
    p.add_argument("--gps-outage-start", type=float, default=15); p.add_argument("--gps-outage-end", type=float, default=45)
    p.add_argument("--seed", type=int, default=11); p.add_argument("--output", type=Path, default=Path("artifacts"))
    a = p.parse_args(); rows = simulate(a.duration, a.gps_outage_start, a.gps_outage_end, a.seed)
    a.output.mkdir(parents=True, exist_ok=True)
    with (a.output / "navigation.csv").open("w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    (a.output / "summary.json").write_text(json.dumps(metrics(rows), indent=2), encoding="utf-8")
    print(json.dumps(metrics(rows), indent=2))


if __name__ == "__main__": main()
