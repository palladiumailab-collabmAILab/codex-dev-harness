[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$CodexSkillsRoot,
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$ManifestPath
)

Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot 'harness-provenance.ps1')

try {
    $resolvedSkillsRoot = Resolve-HarnessDirectory -Path $CodexSkillsRoot
    $resolvedManifestPath = Resolve-HarnessManifestPath -ManifestPath $ManifestPath
    $errors = @(Test-HarnessManifest -ManifestPath $resolvedManifestPath -CodexSkillsRoot $resolvedSkillsRoot)
    if ($errors.Count -gt 0) {
        $errors | ForEach-Object { Write-Error $_ }
        exit 1
    }

    Write-Output "Validated harness manifest: $resolvedManifestPath"
    exit 0
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}
