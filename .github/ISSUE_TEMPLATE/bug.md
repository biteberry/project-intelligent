---
name: Bug
about: Something is broken or producing incorrect output in the pipeline.
title: "[BUG] "
labels: type:bug
assignees: ''
---

## What is wrong
<!-- Describe what is happening vs what should happen -->

## Where it was found
<!-- Pipeline job (J01-J09), layer (Bronze/Silver/Gold/DynamoDB), component -->
**Job:** Jxx
**Layer:** Bronze / Silver / Gold / DynamoDB / Other
**Component:**

## Steps to Reproduce
1. 
2. 
3. 

## Expected Behaviour
<!-- What should have happened -->

## Actual Behaviour
<!-- What actually happened — include log output or DynamoDB record if available -->

## Linked Story or Feature
Affects #<!-- issue number -->

## Fix Acceptance Criteria
- [ ] Root cause identified and documented
- [ ] Fix applied
- [ ] Regression test added
- [ ] Pipeline re-run confirms fix
