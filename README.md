# Karhulaattori

A comprehensive math solver desktop app built with PyQt6, SymPy, NumPy, SciPy, and Matplotlib. Features a Nordic dark theme and 13 specialized tabs covering everything from basic arithmetic to PDEs, graph theory, and complex analysis.

## Installation

### Recommended — uv (installs everything in one command)

If you don't have Git, install it first:

```bash
winget install --id Git.Git -e
```

If you don't have uv, install it:

```bash
winget install --id astral-sh.uv -e
```

Then install and run Karhulaattori:

```bash
uv tool install git+https://github.com/otvainio/Karhulaattori.git
karhulaattori
```

### pip from GitHub

```bash
pip install git+https://github.com/otvainio/Karhulaattori.git
karhulaattori
```

### From source

```bash
git clone https://github.com/otvainio/Karhulaattori.git
cd Karhulaattori
pip install -e .
karhulaattori
```

Python >= 3.10, all dependencies are declared in `pyproject.toml` and installed automatically.

## Tabs

### Calculator
- Standard arithmetic with history sidebar
- Scientific mode: powers, roots, trig (sin/cos/tan), π, e, parentheses
- Variable `x` support with configurable value
- Quick symbolic operations: differentiate, integrate, simplify, solve
- Keyboard shortcuts for all common operations

### Symbolic Solver
- Solve equations and systems of equations (comma-separated)
- Simplify, expand, factor, partial fractions, collect
- Advanced trig: simplify, expand, rewrite in exp/cos
- Logarithm: expand, combine, evaluate in arbitrary base
- LaTeX preview of input and results with copy button
- Interactive graph with pan/zoom, multi-function plotting
  - Explicit, implicit (`x**2 + y**2 = 25`), and vertical lines
  - Automatic x/y-intercepts and intersection points

### Geometry
- **Triangle Solver** — solve any triangle from any 3 knowns (SSS, SAS, ASA, AAS); area, circumradius, inradius
- **Conics** — circle, ellipse, parabola, hyperbola with foci, directrix, asymptotes, eccentricity
- **Shapes** — circle, rectangle, square, equilateral triangle, regular polygon, sector, annulus, trapezoid
- **Transformations** — rotation, reflection, scaling, translation, shear, custom 2×2 matrix; draws original vs. transformed with arrows

### Linear Algebra
- Matrix operations: determinant, inverse, transpose, eigenvalues/vectors, rank, RREF, null space, trace
- Matrix arithmetic: A×B, A+B, scalar multiply
- Vector operations: dot product, cross product, norm, angle, addition, projection
- Solve linear systems Ax = b
- LaTeX output with copy button

### Complex Numbers
- Arithmetic: add, subtract, multiply, divide
- Modulus, argument, conjugate, square, power (De Moivre's theorem)
- Polar form, Euler's formula, rectangular ↔ polar converter
- Argand plane plot

### Calculus
- Derivatives (nth order), definite/indefinite integrals
- Limits, Taylor/Maclaurin series
- Critical points and inflection points
- LaTeX output and input preview
- **Live plots** — tangent line at x₀ for derivatives, shaded area for definite integrals, Taylor polynomial overlaid on f(x), critical points marked on curve

### Differential Equations
- **Symbolic ODE** — dsolve with general/particular solutions, initial condition parser (`y(0)=1, y'(0)=0`), auto-plot; presets for Harmonic, Damped, Forced, Logistic, Bessel, Euler
- **Numerical IVP** — scalar and vector systems; Euler, Heun, RK4, RK45, DOP853, Radau, BDF; phase plane plot for 2D systems; Compare mode
- **Phase Portrait** — autonomous 2D systems; vector field quiver, streamlines, RK45 trajectories, equilibrium finder; presets for SHO, Saddle, Van der Pol, Pendulum, Lotka-Volterra
- **PDE** — finite difference: Heat (FTCS), Wave (leapfrog, CFL check), 2D Laplace (Gauss-Seidel); snapshots at user-specified times

### Statistics
- Descriptive statistics: mean, median, std, variance, quartiles, skewness, kurtosis
- Distributions: Normal, t, Chi-squared, F, Exponential, Poisson, Binomial, Uniform, Beta, Gamma
- Histogram, boxplot, PDF/CDF plots, probability queries
- Combinatorics: factorial, combinations, permutations

### 3D Grapher
- Explicit surfaces `z = f(x, y)` and implicit surfaces `f(x,y,z) = 0` (marching cubes)
- Parametric curves in 3D
- Adjustable colormap, alpha, and axis ranges

### Number Theory
- Primality test, prime factorization, next prime, nth prime
- Euler's totient, divisor count and sigma, Fibonacci
- GCD, LCM, extended Euclidean algorithm
- Modular inverse, Legendre/Jacobi symbols
- Prime counting, prime gaps

### Analysis
- **Fourier** — Fourier series with coefficient plots and approximation; FFT spectrum from discrete signal
- **Special Functions** — Gamma, Digamma, Log-Gamma, Riemann Zeta, Erf/Erfc, Bessel J/Y/I/K, Airy Ai/Bi, Lambert W, Beta; evaluate or plot over range
- **Complex Mapping** — domain colouring, phase portrait, conformal grid mapping, modulus surface for holomorphic functions f(z)
- **Functional Analysis** — Lp norm, sup norm, L² inner product, L² distance, convolution; numerical integration over [a, b]
- **Series & Sums** — convergence tests (Divergence, Ratio, Root, Integral, Alternating Series); exact symbolic sum via SymPy; partial sums convergence plot with exact limit line; clickable common series reference (Basel, harmonic, geometric, e, power series…)

### Numerical Methods
- **Root Finding** — Bisection, Newton-Raphson, Secant, Regula Falsi, Brent; iteration count and convergence plot
- **Integration** — Trapezoidal, Simpson's, Gaussian quadrature, Adaptive (scipy); Compare All mode shows exact SymPy result
- **Interpolation** — Lagrange polynomial, Newton divided differences, Cubic spline, Linear spline; evaluate at arbitrary x
- **Curve Fitting** — Polynomial (any degree), Linear OLS, Exponential, Power law, Custom model (any expression); shows equation and R²

### Graph Theory
- **Graph** — edge list input with directed/weighted toggles; 6 layout algorithms; presets for Petersen, K5, K3,3, Cycle, Tree, DAG
- **Algorithms** — BFS, DFS, Dijkstra, Bellman-Ford, Floyd-Warshall (all-pairs matrix), Topological Sort; highlights path/traversal on graph
- **MST & Coloring** — Kruskal, Prim, Maximum ST; Greedy/Largest-First/DSATUR coloring with color-coded nodes
- **Properties** — degree sequence, connected components, bipartite check, Eulerian path/circuit, adjacency matrix, degree/betweenness centrality

### History
- Persistent cross-tab history (saved to `history.json`)
- Filter by tab, search by keyword
- Export to text file

## Input Syntax

SymPy expression syntax is used throughout:

| Math | Input |
|------|-------|
| x² | `x**2` |
| √x | `sqrt(x)` |
| π | `pi` |
| e | `E` |
| sin(x) | `sin(x)` |
| ln(x) | `log(x)` |
| i (imaginary) | `I` |

**Equation solving:** `x**2 - 4 = 0`  
**System of equations:** `x + y = 5, x - y = 1`  
**ODE:** `y'' - 3*y' + 2*y = 0`  
**Phase portrait:** `f = y`, `g = -x - 0.3*y`  
**Implicit curve:** `x**2 + y**2 = 25`  
**Implicit 3D surface:** `x**2 + y**2 + z**2 = 4`  
**Graph edge list:** `A B 3` (node u, node v, weight)
