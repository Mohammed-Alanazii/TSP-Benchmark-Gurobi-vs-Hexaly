import os
import time
import csv
import argparse
import numpy as np
import tsplib95
import hexaly.optimizer


def load_instance(filepath):
    problem = tsplib95.load(filepath)
    nodes = list(problem.get_nodes())
    n = len(nodes)

    t0 = time.time()
    matrix = [
        [problem.get_weight(nodes[i], nodes[j]) for j in range(n)]
        for i in range(n)
    ]
    load_time = time.time() - t0

    return n, matrix, load_time


def solve(n, matrix, time_limit=60):
    try:
        t0 = time.time()
        with hexaly.optimizer.HexalyOptimizer() as optimizer:
            optimizer.param.verbosity = 0
            model = optimizer.model

            cities = model.list(n)
            model.constraint(model.count(cities) == n)

            dist = model.array(matrix)
            dist_lambda = model.lambda_function(
                lambda i: model.at(dist, cities[i - 1], cities[i])
            )
            obj = (
                model.sum(model.range(1, n), dist_lambda)
                + model.at(dist, cities[n - 1], cities[0])
            )
            model.minimize(obj)
            model.close()
            build_time = time.time() - t0

            optimizer.param.time_limit = time_limit

            t1 = time.time()
            optimizer.solve()
            solve_time = time.time() - t1

            sol = optimizer.solution
            if sol.status.name in ("FEASIBLE", "OPTIMAL"):
                gap = sol.get_objective_gap(0) * 100
                return obj.value, build_time, solve_time, gap
            return None, build_time, solve_time, None

    except Exception as e:
        print(f"Hexaly error: {e}")
        return None, 0, 0, None


def main(instances_dir="instances", time_limit=60, output_csv="Hexaly_results.csv"):
    tsp_files = sorted(f for f in os.listdir(instances_dir) if f.endswith(".tsp"))
    if not tsp_files:
        print(f"No .tsp files found in '{instances_dir}/'")
        return

    print(f"Found {len(tsp_files)} instance(s) in '{instances_dir}/'\n")
    print(f"{'Instance':<28} {'N':>6} {'Obj Value':>15} {'Gap':>7} {'Load':>7} {'Build':>7} {'Solve':>7} {'Total':>7} {'Status':<12}")

    results = []

    for filename in tsp_files:
        filepath = os.path.join(instances_dir, filename)
        name = os.path.splitext(filename)[0]

        try:
            n, matrix, load_time = load_instance(filepath)
        except Exception as e:
            print(f"  {name:<26} {'?':>6}  LOAD ERROR: {e}")
            results.append({"instance": name, "nodes": "?", "obj_value": "N/A",
                            "gap_pct": "N/A", "load_time_s": "N/A", "build_time_s": "N/A",
                            "solve_time_s": "N/A", "total_time_s": "N/A", "status": "LOAD_ERROR"})
            continue

        obj, build_time, solve_time, gap = solve(n, matrix, time_limit)
        total_time = load_time + build_time + solve_time

        if obj is None:
            status, obj_str, gap_str = "N/A", "N/A", "N/A"
        elif gap is not None and gap < 1e-4:
            status, obj_str, gap_str = "OPTIMAL", f"{obj}", f"{gap:.2f}%"
        else:
            status, obj_str, gap_str = "SOLVED", f"{obj}", f"{gap:.2f}%" if gap is not None else "N/A"

        print(f"  {name:<26} {n:>6} {obj_str:>15} {gap_str:>7} "
              f"{load_time:>6.1f}s {build_time:>6.1f}s {solve_time:>6.1f}s {total_time:>6.1f}s  {status:<12}")

        results.append({
            "instance":     name,
            "nodes":        n,
            "obj_value":    str(obj) if obj is not None else "N/A",
            "gap_pct":      f"{gap:.4f}" if gap is not None else "N/A",
            "load_time_s":  f"{load_time:.2f}",
            "build_time_s": f"{build_time:.2f}",
            "solve_time_s": f"{solve_time:.2f}",
            "total_time_s": f"{total_time:.2f}",
            "status":       status,
        })

    print(f"\nDone. {len(results)} instance(s) processed.\n")

    with open(output_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "instance", "nodes", "obj_value", "gap_pct",
            "load_time_s", "build_time_s", "solve_time_s", "total_time_s", "status"
        ])
        writer.writeheader()
        writer.writerows(results)

    print(f"Results saved to '{output_csv}'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hexaly TSP Solver")
    parser.add_argument("--instances",  default="instances",         help="Folder with .tsp files")
    parser.add_argument("--time-limit", type=int, default=60,        help="Solve time limit in seconds")
    parser.add_argument("--output",     default="Hexaly_results.csv", help="Output CSV path")
    args = parser.parse_args()

    main(args.instances, args.time_limit, args.output)