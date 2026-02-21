#!/usr/bin/env python3
"""Sprint management for Ralph Extended.

Creates a compact sprint prd.json from the full backlog.json,
small enough for an AI agent to process efficiently (<100 KB).

Usage:
  python scripts/sprint.py                    # Auto-select next module
  python scripts/sprint.py US-001             # Specific module
  python scripts/sprint.py US-001 US-002      # Multiple modules
  python scripts/sprint.py --status           # Show backlog progress
  python scripts/sprint.py --sync             # Sync prd.json passes back to backlog
"""

import json
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BACKLOG_FILE = os.path.join(PROJECT_ROOT, 'backlog.json')
PRD_FILE = os.path.join(PROJECT_ROOT, 'prd.json')

# Sprint size limit — keep prd.json under this size for reliable AI processing
MAX_SPRINT_KB = 80


def compact_story(story):
    """Make a story compact enough for the sprint prd.json."""
    desc = story.get('description', '')
    if len(desc) > 300:
        desc = desc[:297] + '...'

    criteria = story.get('acceptanceCriteria', [])
    compact_criteria = []
    for c in criteria[:8]:
        if len(c) > 200:
            c = c[:197] + '...'
        compact_criteria.append(c)

    notes = story.get('notes', '')
    if len(notes) > 300:
        notes = notes[:297] + '...'

    return {
        'id': story['id'],
        'title': story['title'],
        'description': desc,
        'acceptanceCriteria': compact_criteria,
        'priority': story['priority'],
        'passes': story['passes'],
        'notes': notes
    }


def load_backlog():
    """Load the full backlog."""
    if not os.path.exists(BACKLOG_FILE):
        print(f'Error: {BACKLOG_FILE} not found.')
        print('')
        print('Create your backlog first:')
        print('  1. Put user stories in docs/userstories/*.md')
        print('  2. python scripts/convert_stories_to_backlog.py')
        print('')
        print('Or create backlog.json manually in prd.json format with many stories.')
        sys.exit(1)
    with open(BACKLOG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def sync_passes_from_prd(backlog):
    """Sync passes status from existing prd.json back to backlog."""
    if not os.path.exists(PRD_FILE):
        return backlog

    try:
        with open(PRD_FILE, 'r', encoding='utf-8') as f:
            prd = json.load(f)
    except (json.JSONDecodeError, KeyError):
        return backlog

    prd_passes = {}
    for s in prd.get('userStories', []):
        if isinstance(s, dict) and s.get('passes'):
            prd_passes[s['id']] = True

    changed = 0
    for story in backlog['userStories']:
        if story['id'] in prd_passes and not story['passes']:
            story['passes'] = True
            changed += 1

    if changed:
        print(f'Synced {changed} newly completed stories to backlog.')

    return backlog


def get_modules(backlog):
    """Get all module prefixes and their story counts."""
    modules = {}
    for s in backlog['userStories']:
        module = s['id'][:6]
        if module not in modules:
            modules[module] = {'total': 0, 'done': 0, 'stories': []}
        modules[module]['total'] += 1
        if s['passes']:
            modules[module]['done'] += 1
        modules[module]['stories'].append(s)
    return modules


def find_next_sprint_modules(backlog):
    """Find the next module(s) to sprint on."""
    modules = get_modules(backlog)
    for module_id in sorted(modules.keys()):
        info = modules[module_id]
        if info['done'] < info['total']:
            return [module_id]
    return []


def create_sprint(backlog, module_ids):
    """Create a sprint prd.json with stories from specified modules."""
    stories = []
    for s in backlog['userStories']:
        module = s['id'][:6]
        if module in module_ids:
            stories.append(compact_story(s))

    stories.sort(key=lambda s: (s['priority'], s['id']))

    total = len(stories)
    done = sum(1 for s in stories if s['passes'])
    remaining = total - done

    module_names = ', '.join(module_ids)
    backlog_total = len(backlog['userStories'])
    backlog_done = sum(1 for s in backlog['userStories'] if s['passes'])

    prd = {
        'project': backlog.get('project', 'MyProject'),
        'branchName': backlog.get('branchName', 'ralph/sprint'),
        'description': (
            f'Sprint: {module_names} — {remaining} of {total} stories remaining. '
            f'Full backlog: {backlog_done}/{backlog_total} complete.'
        ),
        'userStories': stories
    }

    with open(PRD_FILE, 'w', encoding='utf-8') as f:
        json.dump(prd, f, ensure_ascii=False, indent=2)

    size_kb = os.path.getsize(PRD_FILE) // 1024
    print(f'Sprint prd.json created: {module_names}')
    print(f'  Stories: {total} ({done} done, {remaining} remaining)')
    print(f'  File size: {size_kb} KB')
    if remaining > 0:
        print(f'  Highest priority: {min(s["priority"] for s in stories if not s["passes"])}')

    if size_kb > MAX_SPRINT_KB:
        print(f'\n  WARNING: Sprint is {size_kb} KB (limit: {MAX_SPRINT_KB} KB).')
        print(f'  Consider loading fewer modules for better AI performance.')

    return prd


def show_status(backlog):
    """Show backlog progress."""
    modules = get_modules(backlog)
    total_done = sum(m['done'] for m in modules.values())
    total_all = sum(m['total'] for m in modules.values())
    pct = (total_done / total_all * 100) if total_all else 0

    print(f'Backlog: {total_done}/{total_all} stories complete ({pct:.1f}%)\n')

    for mid in sorted(modules.keys()):
        m = modules[mid]
        status = 'DONE' if m['done'] == m['total'] else f'{m["done"]}/{m["total"]}'
        filled = int(m['done'] / max(m['total'], 1) * 20)
        bar = '#' * filled + '.' * (20 - filled)
        print(f'  {mid} [{bar}] {status:>8}')

    # Show current sprint info
    if os.path.exists(PRD_FILE):
        try:
            with open(PRD_FILE, 'r', encoding='utf-8') as f:
                prd = json.load(f)
            sprint_remaining = sum(1 for s in prd.get('userStories', []) if not s.get('passes'))
            sprint_total = len(prd.get('userStories', []))
            size_kb = os.path.getsize(PRD_FILE) // 1024
            print(f'\n  Current sprint: {sprint_remaining}/{sprint_total} remaining ({size_kb} KB)')
        except Exception:
            pass


def main():
    backlog = load_backlog()
    backlog = sync_passes_from_prd(backlog)

    # Save updated backlog
    with open(BACKLOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(backlog, f, ensure_ascii=False, indent=2)

    args = sys.argv[1:]

    if '--status' in args:
        show_status(backlog)
        return

    if '--sync' in args:
        print('Sync complete.')
        return

    # Determine which modules to sprint on
    module_ids = [a.upper() for a in args if a.upper().startswith('US-')]

    if not module_ids:
        module_ids = find_next_sprint_modules(backlog)

    if not module_ids:
        print('All stories complete! Nothing to sprint on.')
        show_status(backlog)
        return

    create_sprint(backlog, module_ids)


if __name__ == '__main__':
    main()
