# Agent Configurations

This directory contains agent role definitions, capabilities, and default configurations for the Graph_x_0x0 8-agent swarm.

## The 8 Agents

```
┌─────────────────────────────────────────────────────┐
│                    ORCHESTRATOR                      │
│   Φ(G) guardian · regime switcher · task router    │
│         Maximizes Φ(G) across all regimes           │
└────────────────────────┬────────────────────────────┘
                         │
      ┌──────────────────┼──────────────────┐
      │                  │                  │
      ▼                  ▼                  ▼
┌──────────┐       ┌──────────┐       ┌──────────┐
│ REFACTOR │       │ QUALITY  │       │   TEST   │
│ Graph    │       │ Code     │       │ Coverage │
│ struct-  │       │ review   │       │ analysis │
│ uring    │       │          │       │          │
└────┬─────┘       └────┬─────┘       └────┬─────┘
     │                  │                  │
     └──────────────────┼──────────────────┘
                        │
               ┌─────────┼─────────┐
               │                   │
               ▼                   ▼
         ┌──────────┐       ┌──────────┐
         │  SKILL   │       │   REPO   │
         │ Skill    │       │ Repo     │
         │ library  │       │ cloning  │
         └────┬─────┘       └────┬─────┘
              │                  │
              └────────┬─────────┘
                       │
                       ▼
                 ┌──────────┐
                 │  BUILD   │
                 │ Multi-   │
                 │ language │
                 └────┬─────┘
                      │
                      ▼
                 ┌──────────┐
                 │ PLANNER  │
                 │ Task     │
                 │ decompo- │
                 │ sition   │
                 └──────────┘
```

## Agent Roles

### 1. Orchestrator Agent
- **Owner of**: Φ(G), regime state
- **Responsibilities**: 
  - Evaluate Φ(G) across all three regimes
  - Trigger regime switches with hysteresis (ΔΦ > 0.05)
  - Route tasks to the appropriate specialist agent
  - Log all regime transitions
- **Communication**: Directs all other agents; receives reports

### 2. Refactor Agent
- **Owner of**: Graph structure (nodes, edges)
- **Responsibilities**:
  - Split oversized nodes (high cyclomatic complexity)
  - Merge redundant edges
  - Move nodes between modules to improve Q(G)
  - Reduce Č(G) by minimizing cross-module dependencies
- **Tools**: Graph mutation primitives, code transformation

### 3. Quality Agent
- **Owner of**: Code quality scores, cyclomatic complexity
- **Responsibilities**:
  - Scan for functions exceeding complexity thresholds
  - Flag quality violations by module
  - Track quality trends over time
  - Recommend refactoring targets
- **Tools**: Static analysis, linting, cyclomatic complexity analysis

### 4. Test Agent
- **Owner of**: Test coverage, test generation
- **Responsibilities**:
  - Measure coverage per module
  - Generate tests for untested functions
  - Identify regression-prone areas
  - Ensure new code has test coverage before commit
- **Tools**: Test runners, coverage tools, test generation

### 5. Skill Agent
- **Owner of**: Skill library
- **Responsibilities**:
  - Load skills on demand
  - Create new skills from successful patterns
  - Update existing skills based on feedback
  - Track skill effectiveness
- **Tools**: File I/O, pattern matching, natural language

### 6. Repo Agent
- **Owner of**: Repository registry
- **Responsibilities**:
  - Clone and track repositories
  - Sync repos and fetch updates
  - Analyze repo graphs
  - Manage multi-repo workspaces
- **Tools**: Git operations, filesystem operations

### 7. Build Agent
- **Owner of**: Build state, language detection
- **Responsibilities**:
  - Detect project languages (Rust, Python, Node, Go, Java, C++)
  - Run builds with appropriate toolchains
  - Parse build output for errors
  - Track build times and trends
- **Tools**: Shell commands, language-specific tools

### 8. Planner Agent
- **Owner of**: Task decomposition
- **Responsibilities**:
  - Break complex tasks into sub-tasks
  - Route sub-tasks to appropriate agents
  - Coordinate multi-agent workflows
  - Track task completion and dependencies
- **Tools**: LLM-based planning, task graphs

## Agent Communication Protocol

All agents communicate through the **shared graph state**:

1. **Agent emits**: Graph mutation (add_node, remove_edge, update_quality)
2. **Orchestrator receives**: Mutation + agent ID + rationale
3. **Orchestrator evaluates**: ΔΦ(G) from mutation
4. **Orchestrator decides**: Commit, reject, or request modification
5. **Orchestrator responds**: Decision + updated Φ(G)

### Example Flow

```
Test Agent → "I found 3 untested functions in module core"
Orchestrator → "What's the impact on Φ(G)?"
Test Agent → "Adding tests: ΔΦ(G) = +0.03 (Č +0.01, mean V +0.02)"
Orchestrator → "Commit. Hybrid regime: +0.03 > 0.05 threshold? No, but within regime."
```

## Regime-Aware Agent Behavior

| Agent | Simple Regime | Advanced Regime | Hybrid Regime |
|-------|-------------|----------------|---------------|
| Orchestrator | Minimize coupling | Maximize modularity | Balance all |
| Refactor | Fast, minimal changes | Thorough restructuring | Moderate changes |
| Quality | Basic linting | Deep review | Standard review |
| Test | Unit tests only | Full coverage | Integration + unit |
| Skill | Reuse existing | Build new skills | Build on-demand |
| Repo | Minimal repos | Deep analysis | Track key metrics |
| Build | Fast builds | Comprehensive | Incremental |
| Planner | Simple plans | Multi-step plans | Tiered plans |

## Adding a New Agent

1. **Define in `agent.rs`**: Add `AgentRole` variant and `Agent` struct
2. **Implement in `swarm.rs`**: Add to `Swarm::new()` and implement `run_<agent>()`
3. **Add to Python**: Mirror in `python/high_agent_engine/agents.py`
4. **Document here**: Add entry to this file

## Configuration

Agents are configured in `~/.high-agent/config.toml`:

```toml
[agents]
max_concurrent = 4
timeout_seconds = 300

[agents.orchestrator]
hysteresis = 0.05
deviation_threshold = 2.0

[agents.quality]
max_cyclomatic = 10
min_quality = 0.7

[agents.test]
min_coverage = 0.8
```
