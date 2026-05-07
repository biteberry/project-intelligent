---
name: Task
about: A concrete implementation task. The smallest unit of trackable work. Always linked to a parent story.
title: "[TASK] "
labels: type:task
assignees: ''
---

## What needs to be done
<!-- Specific, concrete implementation description. Avoid vague language. -->

## Parent Story
Part of #<!-- story issue number -->

## Acceptance Criteria
- [ ] criterion 1 (specific output or behaviour)
- [ ] criterion 2
- [ ] no errors in CloudWatch logs / local log file
- [ ] DynamoDB audit record written (if this is a pipeline job step)

## Files to Create or Modify
<!-- List source files, config files, or schema files this task touches -->
- `src/`
- `configs/`
- `schemas/`

## Test Approach
<!-- How will you verify this task is complete? -->

## Notes
<!-- Gotchas, NSE-specific quirks, AWS free-tier limit considerations -->
