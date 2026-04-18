param(
    [string]$CommitMessage = "",
    [switch]$SkipBundleRebuild,
    [switch]$SkipPush,
    [switch]$SkipProxyDeploy,
    [switch]$ForceProxyDeploy,
    [string]$PublicUrl = "https://fruition-component.pages.dev/"
)

. (Join-Path $PSScriptRoot "powershell_utf8.ps1")

$ErrorActionPreference = "Stop"
$scriptRoot = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $PSCommandPath }
$syncScript = Join-Path $scriptRoot "sync_local_and_public.ps1"
$proxyScript = Join-Path $scriptRoot "deploy_cloudflare_pages_proxy.ps1"

function Test-ProxyPublishNeeded {
    try {
        $statusText = (& git -C $scriptRoot status --porcelain -- cloudflare-pages-proxy/dist cloudflare-pages-proxy/wrangler.jsonc | Out-String).Trim()
        return -not [string]::IsNullOrWhiteSpace($statusText)
    }
    catch {
        return $true
    }
}

if (-not (Test-Path $syncScript)) {
    throw "sync_local_and_public.ps1 not found in $scriptRoot"
}
if (-not (Test-Path $proxyScript)) {
    throw "deploy_cloudflare_pages_proxy.ps1 not found in $scriptRoot"
}

$proxyChanged = Test-ProxyPublishNeeded
$shouldDeployProxy = -not $SkipPush -and -not $SkipProxyDeploy -and ($ForceProxyDeploy -or $proxyChanged)
$proxyChangedLabel = if ($proxyChanged) { "yes" } else { "no" }
$shouldDeployProxyLabel = if ($shouldDeployProxy) { "yes" } else { "no" }

Write-Host ""
Write-Host "=== Public publish plan ==="
Write-Host ("App sync: yes")
Write-Host ("Proxy changes detected: {0}" -f $proxyChangedLabel)
Write-Host ("Proxy deploy: {0}" -f $shouldDeployProxyLabel)
Write-Host ""

try {
    if ([string]::IsNullOrWhiteSpace($CommitMessage)) {
        & $syncScript -PublicUrl $PublicUrl -SkipBundleRebuild:$SkipBundleRebuild -SkipPush:$SkipPush
    }
    else {
        & $syncScript -CommitMessage $CommitMessage -PublicUrl $PublicUrl -SkipBundleRebuild:$SkipBundleRebuild -SkipPush:$SkipPush
    }
}
catch {
    throw
}

if ($shouldDeployProxy) {
    Write-Host ""
    Write-Host "=== Cloudflare Pages proxy deploy ==="
    & $proxyScript
}
elseif ($proxyChanged) {
    Write-Host ""
    Write-Host "Proxy files changed, but proxy deploy was skipped."
    Write-Host "Run deploy_cloudflare_pages_proxy.ps1 if you need to publish the Cloudflare Pages shell."
}

Write-Host ""
Write-Host "Public site: $PublicUrl"
