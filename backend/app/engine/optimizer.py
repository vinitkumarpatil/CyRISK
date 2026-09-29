"""Budget-constrained security investment optimization.

Real 0/1 knapsack (dynamic programming) over candidate investments, scored by
their *modelled* annual-loss reduction. Because control/vuln effects are not
strictly additive, the selected portfolio is then re-simulated jointly and the
true combined ₹ reduction + ROSI are reported. Results change with the budget
and the enterprise state — nothing is hardcoded.
"""
from __future__ import annotations

from .state import clone_state
from . import scenarios

_LAKH = 100_000.0


def _knapsack(items: list, budget_lakh: int) -> list:
    """items: list of dicts with 'cost_lakh' (int) and 'value' (float). Returns chosen indices."""
    n = len(items)
    W = budget_lakh
    dp = [[0.0] * (W + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        ci = items[i - 1]["cost_lakh"]
        vi = items[i - 1]["value"]
        row, prev = dp[i], dp[i - 1]
        for w in range(W + 1):
            row[w] = prev[w]
            if ci <= w:
                cand = prev[w - ci] + vi
                if cand > row[w]:
                    row[w] = cand
    # backtrack
    chosen, w = [], W
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i - 1][w]:
            chosen.append(i - 1)
            w -= items[i - 1]["cost_lakh"]
    chosen.reverse()
    return chosen


# __APPEND_OPTIMIZER__


def optimize(base_state: dict, options: list, budget_inr: float) -> dict:
    """Select the investment portfolio maximizing modelled ALE reduction within budget."""
    baseline = scenarios.evaluate(base_state)
    base_ale = baseline["enterprise"]["total_ale_inr"]

    # Score each option by its individual (marginal) ALE reduction.
    scored = []
    for o in options:
        marginal = scenarios.marginal_ale_reduction(base_state, o, baseline)
        scored.append({
            "key": o["key"], "name": o["name"], "cost_inr": o["cost"],
            "effort": o.get("effort", "Medium"), "control_key": o.get("control_key", ""),
            "category": o.get("category", ""), "action": o.get("action", ""),
            "marginal_ale_reduction_inr": marginal,
            "efficiency": round(marginal / o["cost"], 3) if o["cost"] else 0.0,
            "option": o,
        })

    # Knapsack over affordable, beneficial options.
    budget_lakh = int(round(budget_inr / _LAKH))
    items = [{"idx": i, "cost_lakh": max(1, int(round(s["cost_inr"] / _LAKH))), "value": s["marginal_ale_reduction_inr"]}
             for i, s in enumerate(scored) if s["marginal_ale_reduction_inr"] > 0 and s["cost_inr"] <= budget_inr]
    chosen_local = _knapsack(items, budget_lakh) if items and budget_lakh > 0 else []
    chosen_idx = {items[c]["idx"] for c in chosen_local}

    selected = [s for i, s in enumerate(scored) if i in chosen_idx]
    not_selected = [s for i, s in enumerate(scored) if i not in chosen_idx]

    # Re-simulate the selected portfolio JOINTLY for the true combined effect.
    mutations = []
    for s in selected:
        mutations += scenarios.investment_to_mutations(s["option"])
    joint = scenarios.simulate(base_state, mutations, cost_inr=sum(s["cost_inr"] for s in selected),
                               label="Optimized portfolio", baseline=baseline)

    total_cost = sum(s["cost_inr"] for s in selected)
    marginal_sum = round(sum(s["marginal_ale_reduction_inr"] for s in selected), 2)

    # Build the investment-vs-reduction curve before stripping the option payloads.
    curve = _investment_curve(base_state, scored, baseline)

    for s in scored:
        s.pop("option", None)
    selected.sort(key=lambda s: s["marginal_ale_reduction_inr"], reverse=True)
    not_selected.sort(key=lambda s: s["efficiency"], reverse=True)

    return {
        "budget_inr": budget_inr,
        "baseline": scenarios.key_metrics(baseline),
        "selected": selected, "not_selected": not_selected,
        "selected_count": len(selected),
        "total_cost_inr": total_cost,
        "budget_utilization": round(total_cost / budget_inr, 4) if budget_inr else 0.0,
        "marginal_sum_ale_reduction_inr": marginal_sum,
        "joint_ale_reduction_inr": joint["delta"]["ale_reduction_inr"],
        "joint_ale_reduction_pct": joint["delta"]["ale_reduction_pct"],
        "joint_after": joint["after"],
        "portfolio_rosi_percent": joint["rosi_percent"],
        "note": "Selection is 0/1 knapsack on modelled marginal ALE reduction; the "
                "portfolio is then re-simulated jointly (non-additive), so joint "
                "reduction may differ from the sum of marginals. All figures are modelled estimates.",
        "curve": curve,
    }


def _investment_curve(base_state: dict, scored: list, baseline: dict) -> list:
    """Investment-vs-risk-reduction curve: greedily add options by efficiency,
    re-simulating the cumulative portfolio at each step."""
    ranked = sorted([s for s in scored if s["marginal_ale_reduction_inr"] > 0],
                    key=lambda s: s["efficiency"], reverse=True)
    base_ale = baseline["enterprise"]["total_ale_inr"]
    curve = [{"cumulative_cost_inr": 0.0, "cumulative_ale_reduction_inr": 0.0, "label": "No investment"}]
    mutations, cum_cost = [], 0.0
    for s in ranked:
        mutations += scenarios.investment_to_mutations(s.get("option") or {})
        cum_cost += s["cost_inr"]
        after_state = clone_state(base_state)
        scenarios.apply_mutations(after_state, mutations)
        after = scenarios.evaluate(after_state, run_var=False)
        curve.append({
            "cumulative_cost_inr": round(cum_cost, 2),
            "cumulative_ale_reduction_inr": round(base_ale - after["enterprise"]["total_ale_inr"], 2),
            "label": s["name"],
        })
    return curve
