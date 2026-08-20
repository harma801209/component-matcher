param(
    [Parameter(Mandatory = $true)]
    [string]$Destination,

    [switch]$IncludeGit,
    [switch]$IncludeBackups,
    [switch]$IncludeBrowserProfiles,
    [switch]$IncludeSecrets,
    [switch]$IncludeExternalDocs,
    [string]$ExternalDocsPath = ""
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourceRoot = Split-Path -Parent $scriptDir
$sourceRootFull = [System.IO.Path]::GetFullPath($sourceRoot).TrimEnd("\")
$destinationFull = [System.IO.Path]::GetFullPath($Destination).TrimEnd("\")
$externalDocsFolderName = -join ([char[]](0x88AB, 0x52A8, 0x4EA7, 0x54C1, 0x7EBF, 0x8D44, 0x6599))

if ([string]::IsNullOrWhiteSpace($ExternalDocsPath)) {
    $desktopPath = [Environment]::GetFolderPath("Desktop")
    $ExternalDocsPath = Join-Path $desktopPath $externalDocsFolderName
}

if ($destinationFull.StartsWith($sourceRootFull + "\", [System.StringComparison]::OrdinalIgnoreCase) -or
    $destinationFull.Equals($sourceRootFull, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Destination must not be inside the source workspace: $destinationFull"
}

New-Item -ItemType Directory -Force -Path $destinationFull | Out-Null

$excludeDirs = @(
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".cache",
    "_cloud_sim",
    "_cloudcold_backup",
    "_cf_cookie_copy",
    "local_8532_test_20260429",
    "website_test_20260429",
    "sort_fix_20260429",
    "scratch_loginsetting",
    "scratch_loginsetting2",
    "mlcc_edit_work",
    "tools\PortableGit",
    "tools\nodejs",
    "tools\wrangler",
    "cloudflare-pages-proxy\.wrangler"
)

if (-not $IncludeGit) {
    $excludeDirs += ".git"
}

if (-not $IncludeBrowserProfiles) {
    $excludeDirs += @(
        "streamlit_cloud_profile",
        "chrome_deploy_profile_20260421",
        "chrome_headless_profile",
        "chrome_headless_profile2",
        "chrome_headless_profile3",
        ".selenium-profile",
        "edge_profile_tmp"
    )
}

if (-not $IncludeBackups) {
    $excludeDirs += @(
        "backup",
        "exports",
        "kingdee_network_backup_20260608_164003"
    )
}

$excludeFiles = @(
    "*.log",
    "*.pid",
    "*.tmp",
    "*tmp.*",
    "tmp_*",
    "_tmp_*",
    "battery-report.html",
    "wifi_adapter_before_*.txt",
    "tools\cloudflared.exe"
)

if (-not $IncludeBackups) {
    $excludeFiles += @(
        "*.bak",
        "*.off",
        "*.backup_*",
        "components.db.series_backfill.*"
    )
}

if (-not $IncludeSecrets) {
    $excludeFiles += @(
        "cloudflare_account_api_token.txt",
        "public_access_code.txt",
        "public_fixed_url.txt",
        "public_tunnel_token.txt",
        ".streamlit\secrets.toml"
    )
}

Write-Host "Source:      $sourceRootFull"
Write-Host "Destination: $destinationFull"
Write-Host "IncludeGit: $IncludeGit"
Write-Host "IncludeBackups: $IncludeBackups"
Write-Host "IncludeBrowserProfiles: $IncludeBrowserProfiles"
Write-Host "IncludeSecrets: $IncludeSecrets"
Write-Host ""

$args = @(
    $sourceRootFull,
    $destinationFull,
    "/E",
    "/COPY:DAT",
    "/DCOPY:DAT",
    "/R:2",
    "/W:2",
    "/MT:8",
    "/XJ",
    "/XD"
) + $excludeDirs + @("/XF") + $excludeFiles

& robocopy @args
$robocopyExitCode = $LASTEXITCODE
if ($robocopyExitCode -gt 7) {
    throw "robocopy failed with exit code $robocopyExitCode"
}

if ($IncludeExternalDocs) {
    if (-not (Test-Path -LiteralPath $ExternalDocsPath)) {
        throw "External docs path not found: $ExternalDocsPath"
    }
    $parent = Split-Path -Parent $destinationFull
    if ([string]::IsNullOrWhiteSpace($parent)) {
        $parent = $destinationFull
    }
    $externalDestination = Join-Path $parent $externalDocsFolderName
    New-Item -ItemType Directory -Force -Path $externalDestination | Out-Null
    Write-Host ""
    Write-Host "Copying external source documents:"
    Write-Host "  $ExternalDocsPath"
    Write-Host "  -> $externalDestination"

    & robocopy $ExternalDocsPath $externalDestination /E /COPY:DAT /DCOPY:DAT /R:2 /W:2 /MT:8 /XJ /XF "*.tmp" "*.log"
    $docsExitCode = $LASTEXITCODE
    if ($docsExitCode -gt 7) {
        throw "external docs robocopy failed with exit code $docsExitCode"
    }
}

Write-Host ""
Write-Host "Portable copy completed."
Write-Host "Next step on another PC: create .venv, install requirements.txt, then run start_streamlit.ps1."
