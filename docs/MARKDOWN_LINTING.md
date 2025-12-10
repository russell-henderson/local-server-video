# Markdown Linting

This repository uses [markdownlint-cli](https://github.com/igorshubovych/markdownlint-cli) to ensure all markdown files are error-free and follow consistent formatting rules.

## Installation

Install markdownlint-cli globally using npm:

```bash
npm install -g markdownlint-cli
```

## Configuration

The markdown linting rules are configured in `.markdownlint.json` at the repository root. The configuration uses a balanced approach that enforces important formatting rules while being lenient on documentation-specific requirements:

- **Line length**: Maximum 500 characters (disabled for code blocks, tables, and headings)
- **Disabled rules**:
  - MD013: Line length (configured but very lenient for documentation)
  - MD033: Inline HTML (allowed for flexibility)
  - MD041: First line heading (not required)
  - MD060: Table column style (formatting flexibility)
  - MD024: No duplicate headings (allowed across sections)
  - MD003: Heading style (mixed styles allowed)
  - MD036: Emphasis as heading (allowed)
  - MD045: Image alt text (optional)
  - MD025: Single title (multiple H1s allowed)
  - MD051: Link fragments (anchor validation disabled)
  - MD012: Multiple blank lines (allowed)
  - MD009: Trailing spaces (allowed)

## Running Markdown Linting

### Via Make (Unix/Linux/macOS)

```bash
make lint
```

### Via PowerShell (Windows)

```powershell
.\dev.ps1 lint
```

### Directly with markdownlint

```bash
# Check all markdown files
markdownlint '**/*.md'

# Auto-fix fixable issues
markdownlint '**/*.md' --fix

# Check specific file
markdownlint README.md
```

## Common Issues and Solutions

### Line Too Long

If you encounter line length errors, consider:

1. Breaking long sentences into multiple lines
2. Using bullet points for long lists
3. Adjusting the line_length in `.markdownlint.json` if needed

### Missing Code Language

Always specify the language for fenced code blocks:

```markdown
# Bad
```
code here
```

# Good
```python
code here
```
```

## CI Integration

Markdown linting is integrated into the code quality checks and will run automatically when you use:

- `make lint` on Unix-based systems
- `.\dev.ps1 lint` on Windows

All markdown files must pass linting before changes are committed.

## Further Reading

- [markdownlint rules documentation](https://github.com/DavidAnson/markdownlint/blob/main/doc/Rules.md)
- [markdownlint-cli GitHub](https://github.com/igorshubovych/markdownlint-cli)
