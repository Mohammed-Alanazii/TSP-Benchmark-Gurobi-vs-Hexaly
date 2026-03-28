import os
import time
import csv
import argparse
import numpy as np
import tsplib95
import gurobipy as gp
from gurobipy import GRB


def load_instance(filepath):
    problem = tsplib95.load(filepath)
    nodes = list(problem.get_nodes())
    n = len(nodes)

    t0 = time.time()
    matrix = np.zeros((n, n))
    for i, u in enumerate(nodes):
        for j, v in enumerate(nodes):
            if i != j:
                matrix[i, j] = problem.get_weight(u, v)

    problem.dimension = n
    problem.matrix = matrix
    problem.load_time = time.time() - t0
    return problem


def subtour_callback(model, where, x, n):
    if where != GRB.Callback.MIPSOL:
        return
    vals = model.cbGetSolution(x)
    adj = {i: [] for i in range(n)}
    for i in range(n):
        for j in range(n):
            if vals[i, j] > 0.5:
                adj[i].append(j)
    visited = [False] * n
    for start in range(n):
        if visited[start]:
            continue
        cycle, curr = [], start
        while not visited[curr]:
            visited[curr] = True
            cycle.append(curr)
            curr = adj[curr][0] if adj[curr] else curr
        if len(cycle) < n:
            model.cbLazy(
                gp.quicksum(x[u, v] for u in cycle for v in cycle if u != v)
                <= len(cycle) - 1
            )


def solve(instance, time_limit=60):
    n = instance.dimension
    dist = instance.matrix

    try:
        m = gp.Model("TSP")
        m.setParam("OutputFlag", 0)
        m.setParam("TimeLimit", time_limit)
        m.setParam("MIPGap", 0.0)
        m.Params.LazyConstraints = 1

        t0 = time.time()
        x = m.addVars(n, n, vtype=GRB.BINARY, name="x")
        m.setObjective(
            gp.quicksum(dist[i, j] * x[i, j] for i in range(n) for j in range(n) if i != j),
            GRB.MINIMIZE
        )
        m.addConstrs(x.sum(i, "*") == 1 for i in range(n))
        m.addConstrs(x.sum("*", j) == 1 for j in range(n))
        build_time = time.time() - t0

        t1 = time.time()
        m.optimize(lambda model, where: subtour_callback(model, where, x, n))
        solve_time = time.time() - t1

        if m.SolCount > 0:
            return m.ObjVal, build_time, solve_time, m.MIPGap * 100
        return None, build_time, solve_time, 100.0

    except Exception as e:
        print(f"Gurobi error: {e}")
        return None, 0, 0, 100.0


def main(instances_dir="instances", time_limit=60, output_csv="Gurobi_results.csv"):
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
            instance = load_instance(filepath)
            n, load_time = instance.dimension, instance.load_time
        except Exception as e:
            print(f"  {name:<26} {'?':>6}  LOAD ERROR: {e}")
            results.append({"instance": name, "nodes": "?", "obj_value": "N/A",
                            "gap_pct": "N/A", "load_time_s": "N/A", "build_time_s": "N/A",
                            "solve_time_s": "N/A", "total_time_s": "N/A", "status": "LOAD_ERROR"})
            continue

        obj, build_time, solve_time, gap = solve(instance, time_limit)
        total_time = load_time + build_time + solve_time

        if obj is None:
            status, obj_str, gap_str = "NO_SOLUTION", "N/A", "N/A"
        elif gap < 1e-4:
            status, obj_str, gap_str = "OPTIMAL", f"{obj:.2f}", f"{gap:.2f}%"
        else:
            status, obj_str, gap_str = "TIME_LIMIT", f"{obj:.2f}", f"{gap:.2f}%"

        print(f"  {name:<26} {n:>6} {obj_str:>15} {gap_str:>7} "
              f"{load_time:>6.1f}s {build_time:>6.1f}s {solve_time:>6.1f}s {total_time:>6.1f}s  {status:<12}")

        results.append({
            "instance":     name,
            "nodes":        n,
            "obj_value":    f"{obj:.2f}" if obj is not None else "N/A",
            "gap_pct":      f"{gap:.4f}" if obj is not None else "N/A",
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
    parser = argparse.ArgumentParser(description="Gurobi TSP Solver")
    parser.add_argument("--instances",   default="instances",        help="Folder with .tsp files")
    parser.add_argument("--time-limit",  type=int, default=60,       help="Solve time limit in seconds")
    parser.add_argument("--output",      default="Gurobi_results.csv", help="Output CSV path")
    args = parser.parse_args()

    main(args.instances, args.time_limit, args.output)