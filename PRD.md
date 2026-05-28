# PRD: Assumption Sniper

## 1. Overview

### Product Name

Assumption Sniper

### Tagline

AI that finds the flaws in your thinking before reality does.

### Problem Statement

Most AI products generate ideas, summaries, or answers. Very few systems critically analyze the assumptions behind decisions, startup ideas, architectures, or plans.

People often fail because of:

* hidden assumptions
* operational blind spots
* unrealistic dependencies
* survivorship bias
* untested edge cases

Current workflows rely on:

* human reviewers
* expensive consultants
* delayed real-world feedback

There is no fast, interactive system designed specifically for structured idea stress-testing.

---

# 2. Product Vision

Build an AI-powered cognitive debugging platform that:

* decomposes ideas into assumptions
* identifies weak logical foundations
* simulates edge-case failures
* generates structured critiques
* reconstructs stronger versions of the original idea

The product should feel like:

* an AI strategist
* a systems thinker
* a skeptical co-founder
* a logic auditor

Not a chatbot.

---

# 3. Target Users

## Primary Users

* startup founders
* product managers
* engineers
* students in hackathons
* researchers
* consultants

## Secondary Users

* investors
* debate communities
* business analysts
* UX researchers
* policy planners

---

# 4. Core Features

## 4.1 Input Analysis Engine

### Description

Accepts:

* startup ideas
* project plans
* technical architectures
* product strategies
* policies
* workflows

### Example Input

“We should build a campus delivery app for students.”

### Output

Structured decomposition:

* target users
* goals
* dependencies
* assumptions
* operational requirements

---

## 4.2 Assumption Extraction Engine

### Purpose

Identify all hidden assumptions required for the idea to succeed.

### Functional Requirements

* recursively extract assumptions
* build parent-child assumption chains
* classify assumptions by category

### Categories

* financial
* behavioral
* technical
* operational
* legal
* scalability
* adoption

### Example

Students will use the app

* students need fast delivery
* students trust delivery agents
* students have purchasing power

---

## 4.3 Skeptic Mode

### Purpose

Actively attack the idea.

### Functional Requirements

* generate objections
* identify unrealistic expectations
* detect vague claims
* expose operational risks

### Example

Assumption:
“Students care about delivery speed.”

Critique:
“Most purchases may be pre-planned, reducing urgency demand.”

---

## 4.4 Edge Case Simulator

### Purpose

Stress-test ideas under abnormal conditions.

### Simulated Conditions

* server outages
* peak traffic
* bad weather
* exam periods
* fraud attempts
* low internet connectivity
* supply chain failures

### Output

Failure likelihood and impact assessment.

---

## 4.5 Confidence Scoring

### Metrics

Each assumption receives:

* confidence score
* dependency weight
* impact severity
* evidence strength

### Scoring Scale

0 to 100

---

## 4.6 Reconstruction Engine

### Purpose

Improve weak ideas.

### Functional Requirements

* narrow scope
* reduce risk
* improve differentiation
* increase feasibility

### Example

Original:
“Campus delivery app”

Rebuilt:
“Late-night emergency essentials delivery for hostellers during exams.”

---

## 4.7 Multi-Agent Debate System

### Agents

* investor
* engineer
* marketer
* competitor
* customer
* operations lead

Each agent critiques independently.

---

## 4.8 Visualization Dashboard

### Components

* assumption graph
* dependency tree
* risk heatmap
* confidence radar
* contradiction map

### UX Goal

Transform abstract reasoning into visual intelligence.

---

# 5. User Flow

## Step 1

User submits idea.

## Step 2

System decomposes idea.

## Step 3

Assumptions are extracted.

## Step 4

Skeptic agent attacks assumptions.

## Step 5

Edge cases are simulated.

## Step 6

Scores and risks are calculated.

## Step 7

System generates improved version.

## Step 8

Dashboard displays:

* risks
* weak assumptions
* contradiction points
* rebuilt strategy

---

# 6. Technical Architecture

## Frontend

### Stack

* Next.js
* React
* TailwindCSS
* Framer Motion
* D3.js or React Flow

### Responsibilities

* graph rendering
* dashboard UI
* interactive exploration
* live streaming results

---

## Backend

### Stack

* FastAPI
* Python
* Redis
* PostgreSQL

### Responsibilities

* orchestration
* prompt routing
* caching
* scoring logic
* session storage

---

## AI Layer

### Provider

OpenRouter

### Model Roles

#### Model 1

Idea decomposition

#### Model 2

Assumption extraction

#### Model 3

Skeptic reasoning

#### Model 4

Edge-case simulation

#### Model 5

Reconstruction and optimization

---

# 7. Prompting Strategy

## Assumption Prompt

“Extract all assumptions required for this idea to succeed.”

## Skeptic Prompt

“Act as a hostile critic and identify why this may fail.”

## Edge Case Prompt

“Generate realistic operational failure scenarios.”

## Reconstruction Prompt

“Rebuild this idea into a more viable and defensible version.”

---

# 8. Database Schema

## Tables

### users

* id
* email
* created_at

### projects

* id
* user_id
* title
* input_text
* created_at

### assumptions

* id
* project_id
* assumption_text
* category
* confidence_score
* impact_score

### critiques

* id
* project_id
* critique_text
* severity

### simulations

* id
* project_id
* scenario
* impact

---

# 9. MVP Scope

## Included

* text input
* assumption extraction
* skeptic analysis
* edge-case simulation
* reconstruction engine
* dashboard visualization

## Excluded

* authentication providers
* team collaboration
* web search validation
* historical startup analysis

---

# 10. Future Features

## Live Web Validation

Validate assumptions against:

* Reddit
* market reports
* public datasets
* trends

---

## Persistent User Intelligence

Track recurring logical weaknesses.

Example:
“You consistently underestimate operational complexity.”

---

## Team Debate Rooms

Multiple users collaborate and challenge ideas in real time.

---

## API Access

Allow companies to integrate cognitive debugging into workflows.

---

# 11. Success Metrics

## Product Metrics

* average session duration
* ideas analyzed per user
* rebuild acceptance rate
* returning users

## AI Metrics

* critique relevance
* hallucination rate
* assumption extraction accuracy
* edge-case diversity

---

# 12. Risks

## Technical Risks

* repetitive AI outputs
* hallucinated assumptions
* high inference costs
* latency from multi-agent pipelines

## Product Risks

* users expecting definitive answers
* over-complex UI
* critique fatigue

---

# 13. Competitive Advantage

Unlike standard AI tools:

* this product critiques rather than generates
* focuses on reasoning structures
* creates visual logic intelligence
* simulates adversarial thinking

The differentiation is the transformation of AI from:
“answer generator”
to
“cognitive stress-testing system.”

---

# 14. Launch Strategy

## Initial Audience

* hackathons
* startup communities
* indie hackers
* engineering students

## Demo Strategy

Use intentionally flawed startup ideas and show:

* assumption extraction
* risk visualization
* improved reconstruction

This creates highly visual and memorable demos.

---

# 15. Final Product Goal

Create a system that becomes:

* Grammarly for thinking
* unit testing for ideas
* static analysis for human decisions
* a cognitive debugging platform that helps people find and fix the flaws in their thinking before reality does.

---

# 16. V1 Outcomes and Non-Goals

## Outcomes

* end-to-end run from idea to reconstruction with critiques, edge cases, and scores
* interactive dashboard with assumption graph, dependency tree, risk heatmap, and confidence radar
* shareable report with top risks and rebuilt idea
* saved project history for returning users

## Non-Goals

* general-purpose chatbot or assistant
* market research or live web validation
* team collaboration or real-time co-editing
* automated decisions or guarantees of success
* industry-specific compliance certification

---

# 17. Success Metrics and Quality Bars

## Product Targets (90-day post-launch)

* average session duration >= 6 minutes
* ideas analyzed per active user per week >= 2.0
* rebuild acceptance rate >= 40%
* 4-week returning users >= 25%

## AI Quality Targets

* critique relevance mean >= 4.2/5 on weekly human evaluation
* hallucination rate <= 5% of reviewed critiques
* assumption extraction accuracy >= 85% vs a human baseline set
* edge-case diversity >= 4 distinct categories per run

## Quality Bars (gating)

* critique relevance: >= 4/5 on at least 80% of samples
* hallucination rate: <= 3% for high-severity critiques

---

# 18. Performance and Cost Budgets

* time to first insight (p95) <= 8s
* full pipeline completion (p95) <= 60s
* average run cost <= $0.35, p95 run cost <= $0.70
* max tokens per run <= 20k
* concurrency target: 50 parallel runs with a degraded mode after

---

# 19. Data Retention and Privacy

## Retention

* raw inputs and outputs: 30 days by default
* project summaries and scores: 12 months
* anonymized metrics: 24 months
* backups: rolling 30 days

## Deletion

* user-initiated deletion completes within 7 days
* backups expire and purge on the next rotation window

## Privacy and Legal Constraints

* no training on user data by default
* comply with GDPR and CCPA requests
* store only necessary PII (email and account id)
* prohibit sensitive data in inputs and show warnings
* age gate: 16+

---

# 20. Risk Register and Mitigation Owners

| risk | impact | mitigation | owner |
| --- | --- | --- | --- |
| repetitive or low-variance outputs | low trust | prompt diversity, evals, regression tests | ai lead |
| hallucinated assumptions | misleading decisions | validation, severity gating, audit samples | ai lead |
| high inference costs | margin erosion | caching, routing, budget guards | eng lead |
| latency spikes | drop-off | queueing, timeouts, partial streaming | platform | 
| critique fatigue | churn | summarize top issues, ux pacing | product |

---

# 21. Prod Readiness Criteria

* success metrics and quality bars met for 3 consecutive weeks
* p95 latency within budget at target load
* security review has no critical or high findings open
* backup and restore tested end-to-end
* on-call, alerts, and runbooks in place
* incident response drill completed
* privacy policy, terms, and DPA ready
* staged rollout and rollback verified