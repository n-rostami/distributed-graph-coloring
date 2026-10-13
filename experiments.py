"""Runs the three experiments and writes CSVs + plots to results/.

    python experiments.py
"""
import csv
import os
import random
import statistics

import matplotlib
matplotlib.use("Agg")  # headless/CI-safe backend, must be set before pyplot is imported
import matplotlib.pyplot as plt  # noqa: E402

from network import CycleNetwork, cole_vishkin_palette_schedule, log_star  # noqa: E402
from node import SymmetryBreakingError  # noqa: E402
from validator import Validator as V  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
os.makedirs(OUT, exist_ok=True)


def write_csv(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def exp1_scaling(trials=5):
    """Rounds / messages / state vs n, with IDs drawn from {0..n^3-1}."""
    rows = []
    for k in range(3, 17):
        n = 2 ** k
        N = n ** 3
        rounds, msgs, bits, state = [], [], [], []
        for t in range(trials):
            net = CycleNetwork(n, N, seed=1000 * k + t)
            net.execute_simulation()
            rounds.append(net.rounds_executed)
            msgs.append(net.message_complexity)
            bits.append(net.message_bits)
            state.append(max(net.node_local_state_size_track))
        rows.append([n, N.bit_length(), log_star(n), statistics.mean(rounds), min(rounds), max(rounds),
                     statistics.mean(msgs), statistics.mean(bits), max(state)])
        print(
            f"n=2^{k:<2} rounds={rows[-1][3]:.1f} log*n={log_star(n)} "
            f"msgs={rows[-1][6]:.0f} peak_state_bits={rows[-1][8]}"
        )
    write_csv("exp1_scaling.csv",
              ["n", "id_bits", "log_star_n", "rounds_mean", "rounds_min", "rounds_max",
               "messages_mean", "message_bits_mean", "peak_state_bits"], rows)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot([r[0] for r in rows], [r[3] for r in rows], "o-", label="simulated rounds (IDs < n³)")
    ax.plot([r[0] for r in rows], [r[2] for r in rows], "s--", label="log* n")
    ax.set_xscale("log", base=2)
    ax.set_xlabel("n (cycle length)")
    ax.set_ylabel("rounds")
    ax.set_ylim(0, 10)
    ax.set_title("Cole–Vishkin 3-coloring: rounds vs n")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "rounds_vs_n.png"), dpi=150)
    plt.close(fig)


def exp2_id_space(n=1000):
    """Fix n, blow up the ID space N = 2^(2^j) and watch the staircase."""
    rows = []
    for j in range(2, 13):
        N = 2 ** (2 ** j)
        if N < n:
            continue
        net = CycleNetwork(n, N, seed=j)
        net.execute_simulation()
        cv_rounds = len(cole_vishkin_palette_schedule(N)) - 1
        rows.append([j, 2 ** j, log_star(N), cv_rounds, net.rounds_executed])
        print(f"N=2^(2^{j:<2}) log*N={log_star(N)} CV rounds={cv_rounds} total rounds={net.rounds_executed}")
    write_csv("exp2_id_space.csv", ["j", "id_bits", "log_star_N", "cv_rounds", "total_rounds"], rows)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.step([r[1] for r in rows], [r[4] for r in rows], where="post", label="total rounds (n=1000)")
    ax.plot([r[1] for r in rows], [r[2] for r in rows], "s--", label="log* N")
    ax.set_xscale("log", base=2)
    ax.set_xlabel("bits per ID (log₂ N)")
    ax.set_ylabel("rounds")
    ax.set_title("Rounds vs size of the ID space (n = 1000)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "rounds_vs_idspace.png"), dpi=150)
    plt.close(fig)


def exp3_anonymous(rules_per_setting=300):
    """Anonymous cycle: random deterministic rules never produce a proper coloring."""
    rows = []
    for n in (3, 10, 100, 1000):
        for rounds in (1, 5, 20):
            proper = 0
            identical = 0
            for r in range(rules_per_setting):
                rng = random.Random(f"{n}-{rounds}-{r}")
                table = {}

                def rule(own, succ, pred, table=table, rng=rng):
                    key = (own, succ, pred)
                    if key not in table:
                        table[key] = rng.randrange(8)
                    return table[key]

                net = CycleNetwork(n, anonymous=True)
                net.run_generic_rounds(rule, rounds)
                identical += net.all_states_identical()
                proper += V.is_proper_coloring([s % 3 for s in net.colors])
            rows.append([n, rounds, rules_per_setting, identical, proper])
            print(
                f"anonymous n={n:<5} rounds={rounds:<3} rules={rules_per_setting} "
                f"identical_states={identical} proper_colorings={proper}"
            )

    write_csv(
        "exp3_anonymous.csv",
        ["n", "rounds", "rules_tried", "runs_all_nodes_identical", "runs_proper"],
        rows,
    )

    # indistinguishability: number of distinct radius-r views
    view_rows = []
    n = 60
    for radius in (0, 1, 2, 5, 10):
        anon = CycleNetwork(n, anonymous=True).count_distinct_views(radius)
        ided = CycleNetwork(n, seed=7).count_distinct_views(radius)
        view_rows.append([n, radius, anon, ided])
        print(f"n={n} radius={radius}: distinct views anonymous={anon}, with IDs={ided}")
    write_csv(
        "exp3_views.csv",
        ["n", "radius", "distinct_views_anonymous", "distinct_views_with_ids"],
        view_rows,
    )

    try:
        CycleNetwork(50, anonymous=True).execute_simulation()
    except SymmetryBreakingError as e:
        print("Cole–Vishkin on anonymous cycle ->", type(e).__name__)


if __name__ == "__main__":
    print("== Experiment 1: scaling with n ==")
    exp1_scaling()
    print("\n== Experiment 2: scaling with ID space ==")
    exp2_id_space()
    print("\n== Experiment 3: anonymous cycles ==")
    exp3_anonymous()

