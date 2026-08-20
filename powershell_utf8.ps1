# UTF-8 bootstrap for PowerShell-driven tools.
# Keeps Chinese paths, column names, and commit messages intact.
try {
    $utf8 = [System.Text.UTF8Encoding]::new($false)
    [Console]::InputEncoding = $utf8
    [Console]::OutputEncoding = $utf8
    $OutputEncoding = $utf8
    $env:PYTHONUTF8 = "1"
    $env:PYTHONIOENCODING = "utf-8"
    try {
        chcp 65001 | Out-Null
    } catch {
        # Some hosts block chcp; the console encoding changes above are the important part.
    }
} catch {
    # If the host rejects encoding changes, keep the session usable.
}
