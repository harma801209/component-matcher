# PowerShell UTF-8 Rules

The repo treats UTF-8 as the default for PowerShell sessions and script entry points.

Rules:

1. All PowerShell entry scripts must dot-source `powershell_utf8.ps1` before any text processing or external command invocation.
2. Do not paste Chinese column names, model strings, or commit messages directly into ad hoc PowerShell one-liners unless UTF-8 bootstrap is active.
3. For quick experiments, prefer Python here-strings or short helper scripts over inline PowerShell when the command contains non-ASCII text.
4. If a `.cmd` wrapper is used, it must switch the console to UTF-8 before calling PowerShell.

This keeps the shell from turning Chinese literals into `??` and prevents accidental mismatches in searches, selectors, and data extraction commands.
