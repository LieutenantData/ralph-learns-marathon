#!/bin/bash
# Ralph Extended - Sprint-based AI agent loop for large PRDs
# Usage: ./ralph.sh [--tool amp|claude] [max_iterations]
#
# This is the extended version of Ralph that supports large backlogs
# by splitting them into manageable sprint-sized prd.json files.
#
# Workflow:
#   1. Put your user stories in docs/userstories/*.md
#   2. Run: python scripts/convert_stories_to_backlog.py
#   3. Run: python scripts/sprint.py [MODULE_ID]
#   4. Run: bash scripts/ralph/ralph.sh --tool claude 25

set -e

# Parse arguments
TOOL="claude"
MAX_ITERATIONS=10

while [[ $# -gt 0 ]]; do
  case $1 in
    --tool)
      TOOL="$2"
      shift 2
      ;;
    --tool=*)
      TOOL="${1#*=}"
      shift
      ;;
    *)
      if [[ "$1" =~ ^[0-9]+$ ]]; then
        MAX_ITERATIONS="$1"
      fi
      shift
      ;;
  esac
done

if [[ "$TOOL" != "amp" && "$TOOL" != "claude" ]]; then
  echo "Error: Invalid tool '$TOOL'. Must be 'amp' or 'claude'."
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PRD_FILE="$PROJECT_ROOT/prd.json"
BACKLOG_FILE="$PROJECT_ROOT/backlog.json"
PROGRESS_FILE="$SCRIPT_DIR/progress.txt"
ARCHIVE_DIR="$SCRIPT_DIR/archive"
LAST_BRANCH_FILE="$SCRIPT_DIR/.last-branch"

# Preflight checks
if [ ! -f "$PRD_FILE" ]; then
  echo "Error: $PRD_FILE not found."
  echo ""
  if [ -f "$BACKLOG_FILE" ]; then
    echo "backlog.json exists. Create a sprint first:"
    echo "  python scripts/sprint.py"
  else
    echo "No backlog.json either. Create your backlog first:"
    echo "  1. Put user stories in docs/userstories/*.md"
    echo "  2. python scripts/convert_stories_to_backlog.py"
    echo "  3. python scripts/sprint.py"
  fi
  exit 1
fi

# Check how many stories are left
REMAINING=$(python -c "
import json
with open('$PRD_FILE', 'r', encoding='utf-8') as f:
    d = json.load(f)
print(sum(1 for s in d['userStories'] if not s['passes']))
" 2>/dev/null || echo "?")

if [ "$REMAINING" = "0" ]; then
  echo "All stories in current sprint are complete!"
  echo "Load the next sprint: python scripts/sprint.py"
  exit 0
fi

# Archive previous run if branch changed
if [ -f "$PRD_FILE" ] && [ -f "$LAST_BRANCH_FILE" ]; then
  CURRENT_BRANCH=$(python -c "import json; print(json.load(open('$PRD_FILE','r',encoding='utf-8')).get('branchName',''))" 2>/dev/null || echo "")
  LAST_BRANCH=$(cat "$LAST_BRANCH_FILE" 2>/dev/null || echo "")

  if [ -n "$CURRENT_BRANCH" ] && [ -n "$LAST_BRANCH" ] && [ "$CURRENT_BRANCH" != "$LAST_BRANCH" ]; then
    DATE=$(date +%Y-%m-%d)
    FOLDER_NAME=$(echo "$LAST_BRANCH" | sed 's|^ralph/||')
    ARCHIVE_FOLDER="$ARCHIVE_DIR/$DATE-$FOLDER_NAME"

    echo "Archiving previous run: $LAST_BRANCH"
    mkdir -p "$ARCHIVE_FOLDER"
    [ -f "$PRD_FILE" ] && cp "$PRD_FILE" "$ARCHIVE_FOLDER/"
    [ -f "$PROGRESS_FILE" ] && cp "$PROGRESS_FILE" "$ARCHIVE_FOLDER/"
    echo "   Archived to: $ARCHIVE_FOLDER"

    echo "# Ralph Progress Log" > "$PROGRESS_FILE"
    echo "Started: $(date)" >> "$PROGRESS_FILE"
    echo "---" >> "$PROGRESS_FILE"
  fi
fi

# Track current branch
if [ -f "$PRD_FILE" ]; then
  CURRENT_BRANCH=$(python -c "import json; print(json.load(open('$PRD_FILE','r',encoding='utf-8')).get('branchName',''))" 2>/dev/null || echo "")
  if [ -n "$CURRENT_BRANCH" ]; then
    echo "$CURRENT_BRANCH" > "$LAST_BRANCH_FILE"
  fi
fi

# Initialize progress file if it doesn't exist
if [ ! -f "$PROGRESS_FILE" ]; then
  echo "# Ralph Progress Log" > "$PROGRESS_FILE"
  echo "Started: $(date)" >> "$PROGRESS_FILE"
  echo "---" >> "$PROGRESS_FILE"
fi

echo "Starting Ralph Extended - Tool: $TOOL - Max iterations: $MAX_ITERATIONS"
echo "Sprint: $REMAINING stories remaining"
echo ""

for i in $(seq 1 $MAX_ITERATIONS); do
  echo ""
  echo "==============================================================="
  echo "  Ralph Iteration $i of $MAX_ITERATIONS ($TOOL)"
  echo "==============================================================="

  if [[ "$TOOL" == "amp" ]]; then
    OUTPUT=$(cat "$SCRIPT_DIR/CLAUDE.md" | amp --dangerously-allow-all 2>&1 | tee /dev/stderr) || true
  else
    OUTPUT=$(claude --dangerously-skip-permissions --print < "$SCRIPT_DIR/CLAUDE.md" 2>&1 | tee /dev/stderr) || true
  fi

  # Check for completion signal
  if echo "$OUTPUT" | grep -q "<promise>COMPLETE</promise>"; then
    echo ""
    echo "Sprint complete!"

    # Sync passes back to backlog
    if [ -f "$BACKLOG_FILE" ]; then
      python -c "
import json
with open('$PRD_FILE','r',encoding='utf-8') as f: prd=json.load(f)
with open('$BACKLOG_FILE','r',encoding='utf-8') as f: bl=json.load(f)
done={s['id'] for s in prd['userStories'] if s['passes']}
for s in bl['userStories']:
    if s['id'] in done: s['passes']=True
with open('$BACKLOG_FILE','w',encoding='utf-8') as f: json.dump(bl,f,ensure_ascii=False,indent=2)
print(f'Synced {len(done)} completed stories to backlog.json')
" 2>/dev/null || true
    fi

    echo "Load next sprint: python scripts/sprint.py"
    echo "Completed at iteration $i of $MAX_ITERATIONS"
    exit 0
  fi

  echo "Iteration $i complete. Continuing..."
  sleep 2
done

# Sync passes back to backlog even when max iterations reached
if [ -f "$BACKLOG_FILE" ]; then
  python -c "
import json
with open('$PRD_FILE','r',encoding='utf-8') as f: prd=json.load(f)
with open('$BACKLOG_FILE','r',encoding='utf-8') as f: bl=json.load(f)
done={s['id'] for s in prd['userStories'] if s['passes']}
for s in bl['userStories']:
    if s['id'] in done: s['passes']=True
with open('$BACKLOG_FILE','w',encoding='utf-8') as f: json.dump(bl,f,ensure_ascii=False,indent=2)
print(f'Synced {len(done)} completed stories to backlog.json')
" 2>/dev/null || true
fi

echo ""
echo "Ralph reached max iterations ($MAX_ITERATIONS)."
echo "Run again to continue, or load next sprint."
exit 1
