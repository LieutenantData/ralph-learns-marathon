# Ralph Extended

An autonomous AI agent loop for implementing large backlogs of user stories, sprint by sprint.

Ralph Extended solves the problem of the original Ralph choking on large PRD files (100+ stories). It splits a big backlog into manageable sprint-sized chunks that fit within an AI agent's context window.

## How it works

```
backlog.json (full, 400+ stories, ~1 MB)
        │
        ▼
  sprint.py ──► prd.json (1 module, ~30 stories, ~40 KB)
        │
        ▼
   ralph.sh ──► claude/amp processes one story per iteration
        │
        ▼
  prd.json updated (passes: true) ──► synced back to backlog.json
```

## Quick Start

### 1. Copy into your project

```bash
cp -r Ralph_Extended/scripts/ your-project/scripts/
cp Ralph_Extended/.gitignore your-project/  # or merge with existing
mkdir -p your-project/docs/userstories/
```

### 2. Write your user stories

Put markdown files in `docs/userstories/`. Each file = one module.

```
docs/userstories/
├── US-001-authentication.md
├── US-002-data-model.md
├── US-003-api-endpoints.md
└── ...
```

See `docs/userstories/US-001-example.md` for the expected format.

### 3. Generate the backlog

```bash
python scripts/convert_stories_to_backlog.py --project MyApp --branch ralph/sprint
```

This creates `backlog.json` with all stories from all markdown files.

### 4. Create a sprint

```bash
# Auto-select next incomplete module
python scripts/sprint.py

# Or pick specific module(s)
python scripts/sprint.py US-001
python scripts/sprint.py US-001 US-002
```

This creates a compact `prd.json` (~40 KB) with just that module's stories.

### 5. Run Ralph

```bash
bash scripts/ralph/ralph.sh --tool claude 25
```

Ralph will:
- Read `prd.json`
- Pick the highest-priority incomplete story
- Implement it
- Commit with `feat: [Story ID] - [Title]`
- Mark `passes: true`
- Repeat until sprint is done or max iterations reached

### 6. Next sprint

When a sprint completes, Ralph syncs passes back to `backlog.json` automatically. Load the next sprint:

```bash
python scripts/sprint.py          # auto-selects next module
```

### 7. Check progress

```bash
python scripts/sprint.py --status
```

```
Backlog: 28/418 stories complete (6.7%)

  US-001 [#####...............] 27/27     DONE
  US-002 [#...................]  1/30
  US-003 [....................] 0/25
  ...
```

## File Structure

```
your-project/
├── backlog.json                  # Full backlog (all stories, source of truth)
├── prd.json                      # Current sprint (generated, don't edit manually)
├── prd.json.example              # Example format
├── docs/
│   └── userstories/              # User story markdown files
│       ├── US-001-module-a.md
│       └── US-002-module-b.md
└── scripts/
    ├── convert_stories_to_backlog.py   # Markdown → backlog.json
    ├── sprint.py                       # backlog.json → sprint prd.json
    └── ralph/
        ├── ralph.sh                    # Main agent loop
        ├── CLAUDE.md                   # Agent instructions (customize this!)
        ├── progress.txt                # Accumulated learnings (auto-generated)
        └── archive/                    # Archived sprint logs
```

## User Story Markdown Format

Each story in the markdown files should follow this structure:

```markdown
### US-001-01 Story Title

**Priorität:** P1

**Als** [role] **möchte ich** [action], **damit** [benefit].

**Akzeptanzkriterien:**
1. First criterion
2. Second criterion
3. Third criterion

**Technische Hinweise:**
- Technical note or consideration

**Abhängigkeiten:**
- US-001-00 (dependency description)

---
```

### Supported formats

- **Priority**: `P1`/`P2`/`P3`/`P4` or `**Priorität:** 1`
- **Acceptance criteria**: Numbered (`1.`) or checkbox (`- [ ]`)
- **Story ID**: `US-XXX-YY` (3-digit module, 2-digit story)
- **Language**: German and English user story text supported

## Customizing CLAUDE.md

The `scripts/ralph/CLAUDE.md` file contains the instructions for the AI agent. Customize it for your project:

- **Add your tech stack** (framework, database, testing tools)
- **Add project context** (what the app does, domain knowledge)
- **Add coding conventions** (naming, patterns, folder structure)
- **Add priority strategy** (which modules to tackle first)

The default CLAUDE.md is generic. The more project-specific context you add, the better Ralph performs.

## Tips

- **Keep sprints small**: 20-40 stories per sprint works best (~40-80 KB prd.json)
- **Start with foundations**: Auth, data model, and core UI before business logic
- **Customize CLAUDE.md**: Add your tech stack and conventions
- **Review commits**: Ralph commits after each story — review and fix issues between sprints
- **Use progress.txt**: Ralph accumulates learnings across iterations — these improve quality over time
- **Don't edit prd.json**: It's generated. Edit backlog.json or the markdown sources instead

## Commands Reference

| Command | Description |
|---------|-------------|
| `python scripts/convert_stories_to_backlog.py` | Convert markdown → backlog.json |
| `python scripts/sprint.py` | Create next sprint (auto-select module) |
| `python scripts/sprint.py US-001 US-002` | Create sprint for specific modules |
| `python scripts/sprint.py --status` | Show backlog progress |
| `python scripts/sprint.py --sync` | Sync prd.json completions → backlog |
| `bash scripts/ralph/ralph.sh --tool claude 25` | Run Ralph (25 iterations, Claude) |
| `bash scripts/ralph/ralph.sh --tool amp 10` | Run Ralph (10 iterations, Amp) |
