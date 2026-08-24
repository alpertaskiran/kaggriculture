# Kaggriculture Strategy Notes

> This document consolidates the Kaggriculture discussion in the referenced ChatGPT conversation. The current project mirror contains no uploaded notebooks (`sources/` is empty), so notebook-specific details below are limited to what the conversation itself reported.

## 1. What the game is

Kaggriculture is a turn-based farming and market-management game. An agent controls a farm over a fixed season of 720 turns. Each turn it observes the game state and emits a coordinated set of actions involving the farmer, the farmer's hand, and the market. The objective is to turn limited early capital, labor, land, storage, and time into a strong final economic position—typically by producing valuable goods, selling them into demand, and liquidating appropriately at the end.

The important strategic idea is that the game is not won by isolated local reactions. Strong agents plan a complete season route and use narrow feedback controllers to keep execution on that route when the actual state deviates.

## 2. Turns, days, and season timing

The conversation describes a 720-turn season. A practical agent should therefore reason at two resolutions:

- **Turn level:** exact movement, interaction, planting, harvesting, purchasing, selling, and other executable actions.
- **Day/phase level:** economic milestones such as buying the first cow, expanding land, reaching a target herd, switching from investment to production, and liquidating before the terminal state.

The season map is consequently a schedule of milestones rather than a flat list of 720 unrelated commands. Exact turn arrays can be precomputed, but the agent must re-check the live state each turn before applying corrections.

## 3. Actions and events

The conversation identifies three coordinated action surfaces:

1. **Farmer actions** — movement and farm interactions, including navigating to relevant tiles or facilities and carrying out the planned work.
2. **Hand actions** — using or managing the item currently held, such as performing production or farm work that depends on the hand state.
3. **Market actions** — placing, changing, and executing buy/sell orders, with attention to order priority and current demand.

The recurring event/guard categories reported in the notebook review are:

- weeds appearing and requiring repair;
- storage or shed capacity becoming a constraint;
- market ordering and priority changing the result of a sale;
- opponent-sensitive sales, where another agent's behavior affects price or availability;
- terminal liquidation, where inventory and assets must be converted into final value instead of being left stranded.

These are best treated as events that can interrupt a route briefly, not as reasons to abandon the whole strategy.

## 4. How the notebooks share agent implementations

The conversation states that the uploaded notebooks contain executable agent code, not only results. Some submissions are packaged in generated forms, including long `AGENT_SOURCE` strings and large `_ACTIONS_*` arrays. That makes them difficult to read linearly, but the actual route and controller logic is present.

The reported notebook families include:

- V43/V45, with complete season routes and controller logic;
- an adaptive multi-route agent;
- V16, RC5, and V111;
- V27;
- `kaggriculture-findings-from-zero-to-top-meta.ipynb`, which records experiments, successive generations, and rejected ideas;
- `kaggriculture-rank-your-agent.ipynb`, focused on evaluation and ranking rather than one new strategy.

The practical implication is that strategy can be studied concretely by extracting and normalizing the embedded source, comparing functions, and diffing route arrays turn by turn.

## 5. Recurring successful patterns

The strongest recurring pattern is **planned route plus small feedback controllers**:

```text
choose a coherent season plan
        ↓
encode the plan as per-turn actions
        ↓
observe actual game state
        ↓
apply only narrow corrections
        ↓
emit farmer + hand + market actions
```

Successful designs reported in the conversation commonly include:

- a complete season route rather than ad hoc price-triggered decisions;
- explicit route selection among coherent plans;
- economic milestones and target herd/land compositions;
- protection against weeds, storage limits, market-order effects, and terminal waste;
- opponent-aware selling;
- persistent runtime state so the agent remembers its selected route and progress;
- adaptive market horizons, including the V45 discussion of a two-turn versus three-turn premium horizon;
- early branching when a product such as yarn is persistently demanded (the conversation specifically notes an early Yarn branch).

## 6. Failed or fragile patterns

The conversation does not provide a complete catalog of failed experiments, but it implies several failure modes:

- treating strategy as a giant pile of rules such as `if price > x: sell`;
- encoding only local reactions without a capital sequence or endgame plan;
- assuming the planned state will always match the actual state;
- ignoring weeds, storage, market ordering, or opponent behavior until too late;
- failing to liquidate at the terminal boundary;
- making the route unreadable by freezing everything into generated arrays without a separate human-readable specification;
- evaluating only the final score and not comparing the actual code paths that produced it.

These patterns either cause strategic drift or make improvement hard to diagnose.

## 7. Phase-by-phase season map

### Phase 0 — Initial setup

Start from the economic thesis: decide the intended herd, land, crops, main revenue products, and which goods are for internal consumption versus sale. Establish the opening inventory and reserve enough labor/capital to reach the first milestone.

### Phase 1 — Early capital and first production

Use the opening turns to create liquidity and establish the first production loop. The example discussed in the conversation begins with sheep and crops, then targets the first cow within a few days. Avoid spending on expansion that does not advance the selected route.

### Phase 2 — Expansion milestones

Buy the next quadrant or other land expansion when the route can support it. Add cows or sheep according to the chosen plan. Milestones should be concrete—for example, first cow, six cows total, second quadrant, or a yarn-oriented sheep expansion.

### Phase 3 — Specialization and steady state

Once the farm reaches its intended productive configuration, prioritize reliable production, demand-aware sales, and maintenance. The agent should preserve enough storage and labor capacity to avoid interrupting the production loop.

### Phase 4 — Late-season optimization

Use remaining time for the highest-value production and sales opportunities. Apply narrow corrections for market conditions, weeds, storage, and opponent-sensitive order timing. Do not make a late strategic pivot unless the selected route is no longer viable.

### Phase 5 — Terminal liquidation

Convert remaining inventory and useful assets into final value before the season ends. Terminal liquidation is a first-class planned phase, not an emergency afterthought; otherwise goods, orders, or production capacity may have no time to realize value.

## 8. How to develop an agent strategy

Develop the strategy in layers:

1. **Economic thesis:** choose the farm composition, revenue engine, capital sequence, and end condition.
2. **Milestones:** specify target states by day or phase.
3. **Route:** translate milestones into a complete per-turn action schedule.
4. **Controllers:** add only focused guards for known disturbances—state mismatch, weeds, storage, market order, opponents, and liquidation.
5. **Runtime state:** persist route choice, progress, inventory assumptions, and exceptional events.
6. **Evaluation:** run matchups and inspect both score and code. Compare route arrays, market orders, branch conditions, and terminal behavior.

For example, a milk-heavy route might target 11 cows, 4 sheep, and 3 quadrants, using milk, strawberries, and fertilizer as primary revenue. An early-yarn route might target 6 cows and 10 sheep because persistent `YARN_STORE` demand changes the value of wool. These are examples of complete economic routes, not universal prescriptions.

## 9. How to encode a strategy

Keep a readable specification separate from the generated submission representation. A useful structure is:

```python
plan = choose_route(initial_state)
for turn in range(720):
    state = observe()
    action = plan.actions[turn]
    action = repair_weeds_if_needed(action, state)
    action = protect_storage(action, state)
    action = adjust_market_order(action, state, plan)
    action = liquidate_if_terminal(action, state)
    emit_farmer_hand_market(action)
```

The exact implementation may use frozen action arrays or an embedded source string for submission, as the reviewed notebooks reportedly do. However, the source should still expose the economic plan, route-selection logic, guards, and persistent state clearly enough to compare variants such as V43, V45, RC5, or the adaptive agent.

## 10. Practical review checklist

- Is there a coherent season thesis?
- Are day/phase milestones explicit?
- Does every turn emit valid farmer, hand, and market actions?
- Is the route selected once and then protected from unnecessary drift?
- Are weeds, storage, market ordering, and opponents handled?
- Are product demand branches explicit and explainable?
- Is terminal liquidation scheduled?
- Can the embedded/generated code be normalized and diffed?
- Are results compared with the implementation, not only the leaderboard score?

## 11. Current project status

The dedicated notebook folder has been created at `Kaggriculture-notebooks/`. No notebook files were moved because the current project mirror has no `.ipynb` uploads; `sources/` is empty. When the notebooks become available, preserve their filenames in that folder and disambiguate only actual collisions.
