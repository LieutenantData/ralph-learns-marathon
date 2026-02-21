# Example Module - User Stories

> This is an example file showing the expected markdown format.
> Replace this with your actual user stories.

## Rollen

- **Developer**: Implements features
- **User**: End user of the application
- **Admin**: Manages system configuration

## User Stories

### US-001-01 Add priority field to database

**Priorität:** P1

**Als** Developer **möchte ich** ein Priority-Feld in der Datenbank anlegen, **damit** Aufgaben priorisiert gespeichert werden können.

**Akzeptanzkriterien:**
1. Priority column added to tasks table: 'high' | 'medium' | 'low' (default 'medium')
2. Migration generated and runs successfully
3. Typecheck passes

**Technische Hinweise:**
- Use an enum type for the priority field
- Add index for filtering performance

**Abhängigkeiten:**
- None (foundation story)

---

### US-001-02 Display priority indicator on task cards

**Priorität:** P2

**Als** User **möchte ich** die Priorität auf jeder Aufgabenkarte sehen, **damit** ich wichtige Aufgaben auf einen Blick erkennen kann.

**Akzeptanzkriterien:**
- [ ] Each task card shows colored priority badge (red=high, yellow=medium, gray=low)
- [ ] Priority visible without hovering or clicking
- [ ] Responsive on mobile
- [ ] Typecheck passes

**Technische Hinweise:**
- Use shadcn/ui Badge component with color variants
- Consider colorblind-friendly design (add icon alongside color)

**Abhängigkeiten:**
- US-001-01 (database field must exist)

---
