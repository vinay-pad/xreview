# Hello Script Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a tiny shell script that prints `Hello, world!` and a simple test script that verifies the exact output.

**Architecture:** Keep everything at the repo root to avoid unnecessary structure for a one-file script. Use a plain POSIX shell script for the implementation and a second shell script for verification so the plan stays dependency-free and easy to run anywhere.

**Tech Stack:** POSIX shell, `chmod`, `diff`

### Task 1: Add the output check

**Files:**
- Create: `tests/test_hello.sh`
- Test: `tests/test_hello.sh`

**Step 1: Write the failing test**

```sh
#!/bin/sh
set -eu

output="$(./hello.sh)"
expected="Hello, world!"

if [ "$output" != "$expected" ]; then
  printf 'expected: %s\n' "$expected"
  printf 'actual: %s\n' "$output"
  exit 1
fi
```

**Step 2: Run test to verify it fails**

Run: `sh tests/test_hello.sh`
Expected: FAIL with `./hello.sh: not found`

**Step 3: Write minimal implementation**

No implementation in this task.

**Step 4: Run test to verify it still fails for the expected reason**

Run: `sh tests/test_hello.sh`
Expected: FAIL with `./hello.sh: not found`

**Step 5: Commit**

```bash
git add tests/test_hello.sh
git commit -m "test: add hello script verification"
```

### Task 2: Add the hello script

**Files:**
- Create: `hello.sh`
- Modify: `tests/test_hello.sh`
- Test: `tests/test_hello.sh`

**Step 1: Write the failing test**

The failing test already exists in `tests/test_hello.sh`; do not change it unless the expected output changes.

**Step 2: Run test to verify it fails**

Run: `sh tests/test_hello.sh`
Expected: FAIL with `./hello.sh: not found`

**Step 3: Write minimal implementation**

```sh
#!/bin/sh
printf 'Hello, world!\n'
```

Then make it executable:

```bash
chmod +x hello.sh
```

**Step 4: Run test to verify it passes**

Run: `sh tests/test_hello.sh`
Expected: PASS with no output

Optional manual check:

Run: `./hello.sh`
Expected output: `Hello, world!`

**Step 5: Commit**

```bash
git add hello.sh tests/test_hello.sh
git commit -m "feat: add hello script"
```
