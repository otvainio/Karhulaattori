# Changelog

## [Unreleased]

### Added
- **Calculus tab — live plots**
  - Derivative / nth derivative: plots f(x) with a dashed tangent line at x₀ and a red dot at the contact point
  - Definite integral: shaded area under the curve between limits a and b
  - Taylor series: overlays the polynomial approximation on f(x), centered at x₀
  - Critical points: marks all real critical points on the curve
- **Series & Sums subtab** in Analysis
  - Five convergence tests: Divergence, Ratio, Root, Integral, Alternating Series
  - Exact symbolic sum via SymPy
  - Partial sums convergence plot with exact limit reference line
  - Clickable common series reference (Basel, harmonic, geometric, e, power series…)
- **Packaged as installable Python package** — install with `uv tool install git+https://github.com/otvainio/Karhulaattori.git`
  - Entry point: `karhulaattori`
  - History stored in OS user data directory instead of next to source

### Fixed
- Calculus LaTeX formula canvas was blank — matplotlib mathtext does not support `\bigl`/`\bigr`; replaced with `\left(`/`\right)`
- nth derivative showing factored form (e.g. `6(2x²-1)`) instead of expanded polynomial (`12x²-6`); now applies `expand()` to all derivative results
- Calculus plot exceptions could overwrite the symbolic result with "Error"; plot code is now fully isolated from the result display
- Analysis tab spam-clicking crash — replaced `canvas.draw()` with `canvas.draw_idle()` throughout
- Newton divided differences shape mismatch crash
- Label colors too dark (`#4c566a` → `#7b88a8`) across all tabs
- Convergence tests (Ratio, Root, Integral) giving wrong results due to sympy symbol mismatch between `Symbol('n')` and `Symbol('n', positive=True, integer=True)`
- Partial sums plot broken for expressions with powers
- Bogus exact sum shown for divergent series (e.g. `(1+1/n)^n`)

## Earlier history

See git log for full commit history prior to packaging.
