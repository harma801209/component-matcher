Param(
    [string]$ProjectName = "fruition-component",
    [string]$Branch = "main",
    [string]$AccountId = ""
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$tokenVaultPath = Join-Path $root "cloudflare_account_api_token.txt"
$nodeDir = Join-Path $root "tools\\nodejs\\node-v22.22.2-win-x64"
$wranglerCmd = Join-Path $root "tools\\wrangler\\node_modules\\.bin\\wrangler.cmd"
$projectDir = Join-Path $root "cloudflare-pages-proxy"
$distDir = Join-Path $projectDir "dist"

function Resolve-CloudflareApiToken {
    param(
        [string]$VaultPath
    )

    foreach ($value in @($env:CF_API_TOKEN, $env:CLOUDFLARE_API_TOKEN)) {
        if (-not [string]::IsNullOrWhiteSpace($value)) {
            return $value.Trim()
        }
    }

    if (-not (Test-Path $VaultPath)) {
        throw "Cloudflare API token vault not found: $VaultPath"
    }

    $token = (Get-Content $VaultPath -Raw).Trim()
    if ([string]::IsNullOrWhiteSpace($token)) {
        throw "Cloudflare API token vault is empty: $VaultPath"
    }
    return $token
}

function Resolve-CloudflareAccountId {
    param(
        [string]$ExplicitAccountId,
        [string]$ProjectDirectory
    )

    if (-not [string]::IsNullOrWhiteSpace($ExplicitAccountId)) {
        return $ExplicitAccountId.Trim()
    }

    foreach ($value in @($env:CF_ACCOUNT_ID, $env:CLOUDFLARE_ACCOUNT_ID)) {
        if (-not [string]::IsNullOrWhiteSpace($value)) {
            return $value.Trim()
        }
    }

    $cacheCandidates = @(
        (Join-Path $ProjectDirectory ".wrangler\cache\pages.json"),
        (Join-Path $ProjectDirectory ".wrangler\cache\wrangler-account.json")
    )
    foreach ($candidate in $cacheCandidates) {
        if (-not (Test-Path $candidate)) {
            continue
        }
        try {
            $json = Get-Content $candidate -Raw | ConvertFrom-Json
            foreach ($field in @("account_id", "id")) {
                $value = $json.$field
                if (-not [string]::IsNullOrWhiteSpace([string]$value)) {
                    return [string]$value
                }
            }
        }
        catch {
            continue
        }
    }

    return "473ae5b660837990715648b2bc44619c"
}

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
$env:NODE_OPTIONS = "--dns-result-order=ipv4first"
$cloudflareApiToken = Resolve-CloudflareApiToken -VaultPath $tokenVaultPath
$cloudflareAccountId = Resolve-CloudflareAccountId -ExplicitAccountId $AccountId -ProjectDirectory $projectDir
$env:CF_API_TOKEN = $cloudflareApiToken
$env:CLOUDFLARE_API_TOKEN = $cloudflareApiToken
$env:CF_ACCOUNT_ID = $cloudflareAccountId
$env:CLOUDFLARE_ACCOUNT_ID = $cloudflareAccountId

Push-Location $projectDir
try {
    & $wranglerCmd pages deploy $distDir --project-name $ProjectName --branch $Branch --commit-dirty=true
}
finally {
    Pop-Location
}
