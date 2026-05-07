---
name: opportunity-discovery-engine
description: Continuously identify monetizable opportunities across markets, industries, technologies, regulation, and behavior shifts. Use when asked to find business opportunities, market inefficiencies, emerging trends, asymmetric bets, monetization paths, niche arbitrage, or new ways to make money from changing conditions. Also use when comparing opportunities by expected value, execution difficulty, capital required, and time horizon.
---

# Opportunity Discovery Engine

Identify opportunities that could create financial value for Mark.

## Core lens

For every opportunity scan, look for:
- information asymmetry
- technological disruption
- regulatory change
- mispriced assets, labor, distribution, or risk
- shifts in consumer behavior
- overlooked combinations of existing tools

Default posture: prefer asymmetric opportunities with limited downside and large upside.

## Workflow

### Codebase-to-product extraction variant

Use this variant when the user asks to review an existing app/codebase for revenue strategy, optimization logic, product positioning, business model, or monetizable features.

1. **Find the business logic first**
   - Search source files for domain terms: `revenue`, `goal`, `risk`, `cancel`, `optimization`, `optimizer`, `route`, `savings`, `cost`, `margin`, `AJS`, `conversion`, `retention`, `forecast`.
   - Read the implementation files, not just README/docs; the durable product truth is usually in calculations, thresholds, constants, and UI labels.
   - If available, run lightweight scripts/CLI tools against local sample data to ground claims in real numbers.

2. **Extract the economic model**
   - Identify inputs, formulas, thresholds, defaults, and outputs.
   - Translate code into business language: e.g. `pending revenue × cancellation-rate delta` becomes “revenue rescue from reduced cancellation risk.”
   - Call out duplicated/inconsistent constants because they affect product credibility.

3. **Turn implementation into positioning**
   - Group features by buyer value, not file/module names.
   - Prefer sharp revenue language: “recover margin,” “protect revenue,” “find dollars at risk,” “decision support,” “operator command center.”
   - Separate proven logic from heuristic/prototype logic so claims stay credible.

4. **Recommend product narrative**
   - End with a crisp homepage/product positioning angle, core pillars, proof points, and cleanup items before public claims.

## Workflow

1. **Scan for change**
   - Look for recent changes in technology, policy, infrastructure, buyer behavior, costs, or distribution.
   - Prefer fresh signals over stale narratives.

2. **Identify the inefficiency**
   - State exactly what is broken, uneven, delayed, ignored, or under-monetized.
   - If there is no clear inefficiency, it is probably not an opportunity.

3. **Explain the asymmetry**
   - What is the downside?
   - What caps the risk?
   - What creates nonlinear upside?

4. **Map monetization paths**
   Consider one or more of:
   - investing
   - acquiring or aggregating assets
   - building software/tools
   - selling services
   - automation
   - content/information arbitrage
   - lead generation or distribution capture
   - partnerships or resale

5. **Assess competition**
   Score the landscape by:
   - crowding
   - barriers to entry
   - speed advantage
   - proprietary data or workflow advantage
   - access to distribution

6. **Rank the opportunity**
   Rate each one on a 1-5 scale for:
   - expected value
   - ease of execution
   - capital efficiency
   - speed to first dollar
   - durability

7. **Recommend next move**
   End with the smallest high-leverage action that tests the thesis quickly.

## Output format

For each opportunity, use this structure:

### Opportunity: <name>
- **Why now:** <change creating the opening>
- **Inefficiency:** <what is mispriced / overlooked / broken>
- **Asymmetry:** <limited downside vs upside>
- **Monetization paths:** <2-4 realistic ways to make money>
- **Competitive landscape:** <crowded or open; barriers; exploitable edge>
- **Score:** EV <1-5> · Difficulty <1-5> · Capital <1-5> · Horizon <short/medium/long>
- **First move:** <fastest test>

## Ranking rule

Prioritize opportunities that are:
- early but legible
- testable within days or weeks
- low-capital or low-regret to validate
- adjacent to Mark's strengths in systems, automation, operations, storytelling, and business design

## Creativity rule

Do not stop at obvious answers. Always generate:
- one conventional idea
- one tools/automation angle
- one distribution or information-arbitrage angle
- one weird but plausible edge case

## Reality check

Reject ideas that are:
- pure trend-chasing without an edge
- crowded with no distribution advantage
- impossible to test cheaply
- dependent on fantasy assumptions

Strong opinions beat padded hedging. If an idea is weak, say so.
