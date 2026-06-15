# Skills

Skills are reusable, composable units of agent expertise. Each skill is a markdown file with a structured format that the Skill Agent can load, execute, and update at runtime.

## Skill Format

```markdown
---
name: skill-name
category: domain  (e.g. devops, data-science, mlops, web, rust, python)
trigger: "what the user types or context that activates this skill"
---

# Skill Name

Brief description of what this skill does.

## Steps

1. **Step 1** — Description
   ```bash
   exact-command
   ```

2. **Step 2** — Description
   ```bash
   exact-command
   ```

## Verification

```bash
command-to-verify-success
```

## Pitfalls

- Common mistake 1
- Common mistake 2

## Examples

```
example input → expected output
```
```

## Loading Skills

The Skill Agent loads skills from:
- `~/.high-agent/skills/` (user-local)
- `./skills/` (project-local)
- `~/.hermes/skills/` (hermes shared)

### Adding a Skill (runtime)

```
skill add <name>           # Create from current conversation
skill load <name>          # Load an existing skill
skill list                 # List all available skills
skill update <name>        # Update an existing skill
skill delete <name>        # Remove a skill
```

### Adding a Skill (manual)

Create a `.md` file in `~/.high-agent/skills/` following the format above.

## Existing Skills

See subdirectories for categorized skills:
- `devops/` — CI/CD, Docker, Kubernetes, deployment
- `im-setup/` — IM platform configuration (Feishu, WeChat, Telegram, Discord, Slack, DingTalk, Enterprise WeChat)
- `migration/` — OpenClaw migration, data migration patterns

## Managing Skills

Skills can be:
- **Loaded** into the Skill Agent's active context
- **Composed** — multiple skills can be chained
- **Parameterized** — skills accept arguments
- **Versioned** — each update creates a new version

The Skill Agent tracks which skills are loaded, their usage history, and their effectiveness at improving Φ(G).

## Skill ↔ Regime Interaction

Skills interact with the regime system:

| Regime | Skill Behavior |
|--------|---------------|
| Simple | Prefer existing skills over creating new ones |
| Advanced | Build new skills from every interaction |
| Hybrid | Create skills on-demand, review periodically |

## API

### Rust

```rust
use high_agent::SkillManager;

let mut sm = SkillManager::new();
sm.load_from_dir("~/.high-agent/skills/")?;
let skills = sm.list_skills();
for skill in skills {
    println!("{}: {}", skill.name, skill.description);
}
sm.save_skill(&skill)?;
```

### Python

```python
from high_agent_engine import SkillManager

sm = SkillManager()
sm.load_from_dir("~/.high-agent/skills/")
skills = sm.list_skills()
sm.save_skill(name, content)
```
