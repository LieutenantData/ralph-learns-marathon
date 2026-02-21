#!/usr/bin/env python3
"""Convert markdown user stories from docs/userstories/ into backlog.json.

Expected markdown format per story:

    ### US-001-01 Story Title
    **Priorität:** P1
    **Als** [role] **möchte ich** [action], **damit** [benefit].
    **Akzeptanzkriterien:**
    1. First criterion
    2. Second criterion
    **Technische Hinweise:**
    - Technical note
    **Abhängigkeiten:**
    - Dependency
    ---

Also supports:
    - Priority as "**Priorität:** 1" (plain number)
    - Acceptance criteria as "- [ ] Criterion" (checkbox format)
    - Story ID patterns: US-001-01, US-002-15, etc.

Usage:
    python scripts/convert_stories_to_backlog.py
    python scripts/convert_stories_to_backlog.py --dir path/to/stories
    python scripts/convert_stories_to_backlog.py --project MyApp --branch ralph/sprint
"""

import json
import re
import glob
import os
import sys


def parse_priority(text):
    """Convert P1/P2/P3/P4 or plain number to numeric priority."""
    match = re.search(r'P(\d)', text)
    if match:
        return int(match.group(1))
    match = re.search(r'Priorit[aä]t[:\s*]*(\d)', text)
    if match:
        return int(match.group(1))
    return 2


def parse_story(story_text):
    """Parse a single user story markdown block into prd.json format."""
    lines = story_text.strip().split('\n')

    # Extract ID and title from header
    header = lines[0].strip().lstrip('#').strip()
    id_match = re.match(r'(US-\d{3}-\d{2,3})\s*[:.]?\s*(.*)', header)
    if not id_match:
        return None

    story_id = id_match.group(1)
    title = id_match.group(2).strip()

    # Extract priority
    priority = 2
    for line in lines:
        if 'Priorit' in line or 'Priority' in line:
            priority = parse_priority(line)
            break

    # Extract description (Als... möchte ich... damit... / As a... I want... so that...)
    description_lines = []
    in_description = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('**Als**') or stripped.startswith('**Als ') or stripped.startswith('**As a'):
            in_description = True
        if in_description:
            clean = stripped.replace('**', '').strip()
            if clean:
                description_lines.append(clean)
            if ('damit' in stripped.lower() or 'so that' in stripped.lower()) and stripped.endswith('.'):
                in_description = False
                break
        if in_description and (stripped.startswith('**Akzeptanzkriterien') or stripped.startswith('**Acceptance')):
            in_description = False
            break
    description = ' '.join(description_lines)

    # Extract acceptance criteria
    criteria = []
    in_criteria = False
    current_criterion = ''
    for line in lines:
        stripped = line.strip()
        if '**Akzeptanzkriterien' in stripped or '**Acceptance' in stripped:
            in_criteria = True
            continue
        if in_criteria:
            if any(stripped.startswith(p) for p in ['**Priorit', '**Technische', '**Technical', '**Abhängig', '**Depend', '---']):
                if current_criterion:
                    criteria.append(current_criterion.strip())
                break
            num_match = re.match(r'^(\d+)\.\s+', stripped)
            checkbox_match = re.match(r'^-\s*\[[ x]\]\s*', stripped)
            if num_match or checkbox_match:
                if current_criterion:
                    criteria.append(current_criterion.strip())
                if num_match:
                    current_criterion = stripped[num_match.end():]
                else:
                    current_criterion = stripped[checkbox_match.end():]
            elif stripped.startswith('- ') and not stripped.startswith('- ['):
                current_criterion += ' ' + stripped[2:]
            elif stripped and current_criterion:
                current_criterion += ' ' + stripped
    if current_criterion:
        criteria.append(current_criterion.strip())

    clean_criteria = [c.replace('**', '').strip() for c in criteria if c.replace('**', '').strip()]

    # Extract notes (technical hints + dependencies)
    notes_lines = []
    in_notes = False
    for line in lines:
        stripped = line.strip()
        if any(k in stripped for k in ['**Technische Hinweise', '**Technical', '**Abhängigkeiten', '**Depend']):
            in_notes = True
            continue
        if in_notes:
            if stripped.startswith('---') or stripped.startswith('###'):
                break
            if stripped.startswith('- '):
                notes_lines.append(stripped[2:])
            elif stripped and not stripped.startswith('**'):
                notes_lines.append(stripped)
    notes = ' | '.join(notes_lines) if notes_lines else ''

    return {
        'id': story_id,
        'title': title,
        'description': description,
        'acceptanceCriteria': clean_criteria if clean_criteria else ['Story must be implemented and tested'],
        'priority': priority,
        'passes': False,
        'notes': notes
    }


def parse_file(filepath):
    """Parse a markdown file and extract all user stories."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by story headers (### US-XXX-YY)
    story_pattern = (
        r'(###\s+US-\d{3}-\d{2,3}.*?)'
        r'(?=###\s+US-\d{3}-\d{2,3}'
        r'|## [A-ZÄÖÜ]'  # Next section header
        r'|\*Ende'
        r'|\Z)'
    )
    matches = re.findall(story_pattern, content, re.DOTALL)

    stories = []
    for match in matches:
        story = parse_story(match)
        if story:
            stories.append(story)
    return stories


def main():
    # Parse arguments
    stories_dir = None
    project_name = 'MyProject'
    branch_name = 'ralph/sprint'

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '--dir' and i + 1 < len(args):
            stories_dir = args[i + 1]
            i += 2
        elif args[i] == '--project' and i + 1 < len(args):
            project_name = args[i + 1]
            i += 2
        elif args[i] == '--branch' and i + 1 < len(args):
            branch_name = args[i + 1]
            i += 2
        else:
            i += 1

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    if stories_dir is None:
        stories_dir = os.path.join(project_root, 'docs', 'userstories')

    if not os.path.isdir(stories_dir):
        print(f'Error: Stories directory not found: {stories_dir}')
        print(f'Create it and add your user story markdown files (US-*.md).')
        sys.exit(1)

    all_stories = []
    md_files = sorted(glob.glob(os.path.join(stories_dir, 'US-*.md')))

    if not md_files:
        print(f'No US-*.md files found in {stories_dir}')
        sys.exit(1)

    for filepath in md_files:
        filename = os.path.basename(filepath)
        stories = parse_file(filepath)
        print(f'{filename}: {len(stories)} stories')
        all_stories.extend(stories)

    print(f'\nTotal: {len(all_stories)} stories')

    # Preserve passes from existing backlog
    backlog_path = os.path.join(project_root, 'backlog.json')
    if os.path.exists(backlog_path):
        try:
            with open(backlog_path, 'r', encoding='utf-8') as f:
                old = json.load(f)
            old_passes = {s['id'] for s in old.get('userStories', []) if s.get('passes')}
            preserved = 0
            for s in all_stories:
                if s['id'] in old_passes:
                    s['passes'] = True
                    preserved += 1
            if preserved:
                print(f'Preserved {preserved} completed stories from existing backlog.')
        except Exception:
            pass

    backlog = {
        'project': project_name,
        'branchName': branch_name,
        'description': f'Full backlog: {len(all_stories)} stories.',
        'userStories': all_stories
    }

    with open(backlog_path, 'w', encoding='utf-8') as f:
        json.dump(backlog, f, ensure_ascii=False, indent=2)

    size_kb = os.path.getsize(backlog_path) // 1024
    print(f'\nbacklog.json written ({size_kb} KB)')
    print(f'Next: python scripts/sprint.py')


if __name__ == '__main__':
    main()
