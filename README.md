# ralph-learns-marathon

Sprint-based backlog management for the [Ralph](https://github.com/snarktank/ralph) autonomous AI agent loop. Lets Ralph tackle projects with hundreds of user stories by splitting large backlogs into context-window-friendly sprints.

## The Problem

Ralph's original design assumes each `prd.json` fits comfortably in an AI agent's context window. That works for small projects (5-20 stories). But real-world projects often have 100-500+ stories — a `prd.json` that large (1+ MB) fills the entire context window before Ralph writes a single line of code.

## The Solution

```
backlog.json (full, 400+ stories, ~1 MB)  ── never read by the AI agent
        |
        v
  sprint.py ──> prd.json (1 module, ~30 stories, ~40 KB)
        |
        v
   ralph.sh ──> claude/amp processes one story per iteration
        |
        v
  prd.json updated (passes: true) ──> synced back to backlog.json
```

The AI agent only ever sees a small sprint-sized slice of the backlog. Progress is tracked in `backlog.json` across sprints.

## Quick Start

### 1. Copy into your project

```bash
# Clone this repo
git clone https://github.com/YOUR_USERNAME/ralph-learns-marathon.git

# Copy the scripts into your project
cp -r ralph-learns-marathon/scripts/ your-project/scripts/
mkdir -p your-project/docs/userstories/
```

### 2. Write your user stories

Put markdown files in `docs/userstories/`. Each file represents one module.

```
docs/userstories/
├── US-001-authentication.md
├── US-002-data-model.md
├── US-003-api-endpoints.md
└── ...
```

See [`docs/userstories/US-001-example.md`](docs/userstories/US-001-example.md) for the expected format.

### 3. Generate the backlog

```bash
python scripts/convert_stories_to_backlog.py --project MyApp --branch ralph/sprint
```

This parses all markdown files and creates `backlog.json` with every story.

### 4. Create a sprint

```bash
# Auto-select the next incomplete module
python scripts/sprint.py

# Or pick specific module(s)
python scripts/sprint.py US-001
python scripts/sprint.py US-001 US-002
```

This generates a compact `prd.json` (~40 KB) from the selected module's stories.

### 5. Run Ralph

```bash
bash scripts/ralph/ralph.sh --tool claude 25
```

Ralph will pick the highest-priority incomplete story, implement it, commit, mark it as done, and move on — one story per iteration, up to 25 iterations.

### 6. Next sprint

When a sprint completes (or you run out of iterations), progress is automatically synced back to `backlog.json`. Load the next module:

```bash
python scripts/sprint.py
```

### 7. Check progress

```bash
python scripts/sprint.py --status
```

```
Backlog: 28/418 stories complete (6.7%)

  US-001 [####################]    DONE
  US-002 [#...................]    1/30
  US-003 [....................]    0/25
  ...
```

## How It Differs from Standard Ralph

| | Standard Ralph | ralph-learns-marathon |
|---|---|---|
| Max stories | ~20 (must fit in context) | Unlimited |
| Backlog file | `prd.json` (single file) | `backlog.json` + sprint `prd.json` |
| Sprint management | None | `sprint.py` with auto-module detection |
| Cross-sprint sync | None | Automatic pass/fail sync to backlog |
| Progress tracking | None | `--status` with per-module progress bars |
| Markdown import | None | `convert_stories_to_backlog.py` |
| `jq` dependency | Yes | No (pure Python) |
| Preflight checks | None | Validates files, story count, sprint size |

## File Structure

```
your-project/
├── backlog.json                        # Full backlog — source of truth
├── prd.json                            # Current sprint — generated, don't edit
├── docs/
│   └── userstories/                    # User story markdown sources
│       ├── US-001-module-a.md
│       └── US-002-module-b.md
└── scripts/
    ├── convert_stories_to_backlog.py   # Markdown → backlog.json
    ├── sprint.py                       # backlog.json → sprint prd.json
    └── ralph/
        ├── ralph.sh                    # Agent loop (claude / amp)
        ├── CLAUDE.md                   # Agent instructions — customize this!
        ├── progress.txt                # Accumulated learnings (auto-generated)
        └── archive/                    # Archived sprint logs
```

## User Story Format

```markdown
### US-001-01 Story Title

**Priorität:** P1

**Als** [role] **möchte ich** [action], **damit** [benefit].

**Akzeptanzkriterien:**
1. First criterion
2. Second criterion

**Technische Hinweise:**
- Technical note

**Abhängigkeiten:**
- US-001-00 (dependency)

---
```

**Supported variants:**
- Priority: `P1`/`P2`/`P3`/`P4` or `**Priorität:** 1` or `**Priority:** 1`
- Criteria: Numbered (`1.`) or checkbox (`- [ ]`)
- Story IDs: `US-XXX-YY` (3-digit module, 2+ digit story number)
- Languages: German and English

## Customizing CLAUDE.md

`scripts/ralph/CLAUDE.md` is the prompt that drives the AI agent. The default is generic — customize it with:

- Your tech stack (framework, DB, testing)
- Project domain context
- Coding conventions
- Module priority order

The more specific you make it, the better Ralph performs.

## Tips

- **Keep sprints under 80 KB** — 20-40 stories per sprint is the sweet spot
- **Foundation first** — Auth, data model, core UI before business features
- **Review between sprints** — Ralph commits per story, review the batch before continuing
- **Don't edit prd.json** — It's generated. Edit `backlog.json` or the markdown sources
- **progress.txt compounds** — Ralph's learnings carry across iterations and sprints

## Commands

| Command | Description |
|---------|-------------|
| `python scripts/convert_stories_to_backlog.py` | Parse markdown into `backlog.json` |
| `python scripts/sprint.py` | Create next sprint (auto-detect module) |
| `python scripts/sprint.py US-001 US-002` | Sprint for specific modules |
| `python scripts/sprint.py --status` | Show backlog progress |
| `python scripts/sprint.py --sync` | Sync sprint completions back to backlog |
| `bash scripts/ralph/ralph.sh --tool claude 25` | Run 25 iterations with Claude |
| `bash scripts/ralph/ralph.sh --tool amp 10` | Run 10 iterations with Amp |

## Requirements

- Python 3.8+
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) or [Amp](https://ampcode.com)
- Git
- A project with user stories to implement

## Credits

Built on top of the [Ralph pattern](https://github.com/snarktank/ralph) by Geoffrey Huntley. Ralph-learns-marathon extends it with sprint-based backlog management for large-scale projects.

## License

MIT
