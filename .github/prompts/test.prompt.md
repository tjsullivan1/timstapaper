---
mode: 'agent'
model: GPT-5 mini (Preview)
tools: ['codebase', 'editFiles']
description: This prompt will write a test file to the file system as a test
---

Your goal is to generate a new test file (%project_root%/test/test.md), with the following contents:

```markdown
# Test File

This is a test file for the platform engineering mode.

## Test Cases

- [ ] Test case 1
- [ ] Test case 2
- [ ] Test case 3
```