# 🧹 precommit-xml-tools

This repository provides `pre-commit` hooks for formatting XML files using `xmlstarlet` and sorting attributes using `xsltproc`.

---

## ✅ Hooks Included

### 1. `xmlstarlet-format`

Formats XML files with consistent indentation using `xmlstarlet`.

- **Command:** `xmlstarlet fo --indent-spaces 4`
- **Effect:** Pretty-prints XML with 4-space indentation
- **Requirement:** `xmlstarlet`

### 2. `sort-xml`

Sorts XML element attributes alphabetically using XSLT, and then formats the result with `xmlstarlet`.

- **Command:** `xsltproc sort-attrs.xslt | xmlstarlet fo`
- **Effect:** Alphabetically orders attributes in each element and formats
- **Requirement:** `xsltproc`, `xmlstarlet`

### 3. `github-workflow for robo and unit tests`

```
  - repo: https://github.com/Odoo-Ninjas/precommit-hooks
    rev: main
    hooks:
      - id: make_odoo_robot_tests_githubworkflow
        args:
          - .github/workflows/testing.yml
```

---

## 🔧 Usage

1. Install required tools:
   ```bash
   brew install xmlstarlet libxslt   # macOS
   sudo apt install xmlstarlet xsltproc  # Debian/Ubuntu