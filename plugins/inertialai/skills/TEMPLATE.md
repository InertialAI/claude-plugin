<!--
Skill template. Not a runnable skill — placed at skills/TEMPLATE.md (not
inside a subdirectory) so Claude Code's skill discovery skips it.

To add a new skill:
  1. mkdir skills/<your-skill-name>/        (kebab-case, matches `name` below)
  2. Copy this file to skills/<your-skill-name>/SKILL.md
  3. Fill in the frontmatter and sections below; delete any you don't need.
  4. Reload the plugin (/reload-plugins) or restart claude.

Sections used by the existing skills, in order: trigger paragraph,
Cardinal rule (optional), Workflow, Alternative (optional), Guidelines,
Don't (optional). Keep it short — these are playbooks Claude reads on
every invocation, not docs.
-->
---
name: <kebab-case-skill-name>
description: <one sentence describing when Claude should invoke this skill — this is what Claude sees when deciding whether to pick it>
---

Use this skill when the user <describes the trigger condition in plain
language: phrases the user might say, errors they might hit, types of
data they might bring>.

## Cardinal rule

<Optional. Use for a single inviolable rule (e.g. "never accept the API
key in chat"). If there's no such rule, delete this section.>

## Workflow

1. **<Step name>.** <What to do, including which MCP tools to call by name
   and how to interpret the result.>
2. **<Step name>.** <Detail.>
3. **<Step name>.** <Detail.>

## Alternative: <name>

<Optional. Use when there's a second valid approach worth mentioning
(e.g. "classify against a known-normal corpus" in find-anomalies). Delete
if not applicable.>

## Guidelines

- <Rule of thumb that doesn't fit the numbered workflow — performance
  notes, when to sample vs full-scan, defaults, etc.>
- <Another guideline.>

## Don't

- <Optional. Anti-patterns to avoid (e.g. "don't return raw embedding
  vectors"). Delete if redundant with the cardinal rule.>
