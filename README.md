# TSP Solver Benchmark — Gurobi vs Hexaly

In this Jupyter notebook I compare two different solvers head-to-head on the classic Traveling Salesman Problem.

- **Gurobi** tackles TSP as an exact Mixed-Integer Program with lazy subtour elimination constraints. 
- **Hexaly** takes a heuristic approach, using a list-based model with local-search optimization. 
Both are given the same instances and the same time limit — then the notebook does the rest.

---

## What's Inside the Notebook

The notebook (`TSP_Benchmark.ipynb`) runs end-to-end through ten sections:

| # | Section | What It Does |
|---|---------|--------------|
| 1 | **Run Solvers** | Executes both solvers on every `.tsp` file in `instances/` and writes results to CSV |
| 2 | **Load Results** | Reads the CSVs back into Pandas DataFrames |
| 3 | **Side-by-Side Comparison Table** | A color-coded HTML table showing objective value, gap, solve time, total time, and status for each solver |
| 4 | **Solve Time Comparison** | Grouped bar chart of pure solve times |
| 5 | **Total Time Comparison** | Grouped bar chart of end-to-end time (load + build + solve) |
| 6 | **Optimality Gap Comparison** | Bar chart comparing gap to optimality |
| 7 | **Objective Value Comparison** | Bar chart comparing final tour costs |
| 8 | **Time Breakdown (Stacked)** | Stacked bars showing how each solver spends its time across loading, model building, and solving |
| 9 | **Nodes vs Solve Time (Scalability)** | Scatter plot showing how each solver scales with instance size |
| 10 | **Summary Statistics** | Aggregated metrics — average gap, average time, solve rate, and more |

---

## Benchmark Instances

The `instances/` folder contains 10 TSPLIB-format problems ranging from 1,000 to ~7,400 nodes:

| Instance | Nodes |
|----------|------:|
| dsj1000 | 1,000 |
| pcb1173 | 1,173 |
| d2103 | 2,103 |
| pr2392 | 2,392 |
| pcb3038 | 3,038 |
| fl3795 | 3,795 |
| fnl4461 | 4,461 |
| rl5915 | 5,915 |
| rl5934 | 5,934 |
| pla7397 | 7,397 |

You can drop in any additional `.tsp` (TSPLIB format) files and the benchmark will pick them up automatically.

---

## Quick Start

### 1. Install dependencies

```bash
pip install pandas matplotlib numpy tsplib95 gurobipy hexaly
```

> **Note:** Gurobi requires a valid license (free academic licenses are available). Hexaly also requires a license for extended use.

### 2. Run the notebook

```bash
jupyter notebook TSP_Benchmark.ipynb
```

Then run all cells. By default each solver gets **60 seconds** per instance. You can adjust the `TIME_LIMIT` variable in the first code cell.

---

## Running Solvers from the Command Line

Both solvers are standalone scripts that work outside the notebook:

```bash
# Gurobi
python Gurobi_solver.py --instances instances/ --time-limit 60 --output Gurobi_results.csv

# Hexaly
python Hexaly_solver.py --instances instances/ --time-limit 60 --output Hexaly_results.csv
```

---

## Project Structure

```
.
├── TSP_Benchmark.ipynb      # Main benchmark notebook
├── Gurobi_solver.py         # Gurobi TSP solver 
├── Hexaly_solver.py         # Hexaly TSP solver 
├── instances/               # TSPLIB .tsp files (10 instances)
├── plots/                   # Saved chart images
├── Gurobi_results.csv       # Gurobi run results
└── Hexaly_results.csv       # Hexaly run results
```

---

## How the Solvers Work

**Gurobi** — Formulates TSP as a binary integer program with a degree-2 constraint on every node. Subtour eliminated by a lazy constraint, every time the solver finds an integer solution, the lazy constraint detects short cycles and injects a cut. This gives provably optimal solutions, but model building and cut generation become expensive at larger scales.

**Hexaly** — Models the tour as a permutation list and minimizes the total distance using Hexaly's built-in local-search heuristics. No explicit subtour constraints are needed because the list variable naturally represents a single cycle. It finds near-optimal solutions quickly, even on very large instances, which make it a very good and reliable choice in scalable optimization.

---

## Key Takeaway

On smaller instances (up to ~3,800 nodes), Gurobi delivers proven-optimal solutions. Beyond that, model construction becomes the bottleneck and it may not find any feasible solution within the time limit. Hexaly always returns a near-optimal solution with a modest gap (1–5%) and scales more gracefully to the largest instances.
