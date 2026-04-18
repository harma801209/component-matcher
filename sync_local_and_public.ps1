param(
    [string]$CommitMessage = "",
    [switch]$SkipBundleRebuild,
    [switch]$SkipPush,
    [switch]$AllowPublicRuntimeChange,
    [string]$PublicUrl = "https://fruition-component.pages.dev/"
)

. (Join-Path $PSScriptRoot "powershell_utf8.ps1")

$ErrorActionPreference = "Stop"
$scriptRoot = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $PSCommandPath }

function Resolve-PythonInvocation {
    $venvPython = Join-Path $scriptRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        return @($venvPython)
    }

    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        return @("python")
    }

    $pyCmd = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCmd) {
        return @("py", "-3")
    }

    throw "Python not found. Install Python or create .venv first."
}

$pythonCmd = @(Resolve-PythonInvocation)
$syncScript = Join-Path $scriptRoot "sync_local_and_public.py"

if (-not (Test-Path $syncScript)) {
    throw "sync_local_and_public.py not found in $scriptRoot"
}

$argsList = @($syncScript, "--public-url", $PublicUrl)
if (-not [string]::IsNullOrWhiteSpace($CommitMessage)) {
    $argsList += @("--commit-message", $CommitMessage)
}
if ($SkipBundleRebuild) {
    $argsList += "--skip-bundle-rebuild"
}
if ($SkipPush) {
    $argsList += "--skip-push"
}
if ($AllowPublicRuntimeChange) {
    $argsList += "--allow-public-runtime-change"
}

if ($pythonCmd.Length -gt 1) {
    & $pythonCmd[0] @($pythonCmd[1..($pythonCmd.Length - 1)]) @($argsList)
}
else {
    & $pythonCmd[0] @($argsList)
}
if ($LASTEXITCODE -ne 0) {
    throw "sync_local_and_public.py exited with code $LASTEXITCODE"
}
