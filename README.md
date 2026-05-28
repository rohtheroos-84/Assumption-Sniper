# Assumption Sniper

AI that finds the flaws in your thinking before reality does.

## goal
build an AI-powered cognitive debugging platform that decomposes ideas into assumptions, stress-tests them with critiques and edge cases, scores risk, and reconstructs stronger versions.

## core workflow
1. user submits an idea
2. system decomposes goals, dependencies, and assumptions
3. skeptic mode attacks weak logic
4. edge cases are simulated and scored
5. reconstruction proposes a more viable version
6. dashboard visualizes graphs, risk heatmaps, and contradictions

## mvp scope
included: text input, assumption extraction, skeptic analysis, edge-case simulation, reconstruction engine, dashboard visualization
excluded: auth providers, team collaboration, web search validation, historical startup analysis

## stack (planned)
frontend: next.js, react, tailwindcss, framer motion, d3.js or react flow
backend: fastapi, python, redis, postgresql
ai layer: openrouter with role-specific prompts

## outputs
- assumption graph and dependency tree
- risk heatmap and confidence radar
- critiques, edge cases, and rebuilt idea
