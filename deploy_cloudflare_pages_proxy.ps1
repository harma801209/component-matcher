Param(
    [string]$ProjectName = "fruition-component",
    [string]$Branch = "main"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$nodeDir = Join-Path $root "tools\\nodejs\\node-v22.22.2-win-x64"
$wranglerCmd = Join-Path $root "tools\\wrangler\\node_modules\\.bin\\wrangler.cmd"
$projectDir = Join-Path $root "cloudflare-pages-proxy"
$distDir = Join-Path $projectDir "dist"

if (-not (Test-Path $nodeDir)) {
    throw "Node.js portable tool not found: $nodeDir"
}
if (-not (Test-Path $wranglerCmd)) {
    throw "Wrangler tool not found: $wranglerCmd"
}
if (-not (Test-Path $distDir)) {
    throw "Cloudflare Pages dist directory not found: $distDir"
}

$env:PATH = "$nodeDir;$env:PATH"

Push-Location $projectDir
try {
    & $wranglerCmd pages deploy $distDir --project-name $ProjectName --branch $Branch --commit-dirty=true
}
finally {
    Pop-Location
}
