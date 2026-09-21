[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$CodexSkillsRoot,
    [string[]]$Name = @('repo-research', 'github-operations', 'self-improvement', 'long-running-work'),
    [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$ManifestPath,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot 'harness-provenance.ps1')

try {
    $resolvedRepositoryRoot = Resolve-HarnessDirectory -Path $RepositoryRoot
    $resolvedSkillsRoot = Resolve-HarnessDirectory -Path $CodexSkillsRoot -Create
    if ([string]::IsNullOrWhiteSpace($ManifestPath)) {
        $ManifestPath = Join-Path (Split-Path -Parent $resolvedSkillsRoot) 'harness.lock.json'
    }
    $resolvedManifestPath = Resolve-HarnessManifestPath -ManifestPath $ManifestPath
    $plan = Get-HarnessSyncPlan -RepositoryRoot $resolvedRepositoryRoot -CodexSkillsRoot $resolvedSkillsRoot -ManifestPath $resolvedManifestPath -Name $Name

    Write-HarnessSyncPlan -Plan $plan
    if ($plan.conflicts.Count -gt 0) {
        Write-Error 'Sync stopped before changing files because conflicts were detected.'
        exit 2
    }
    if ($DryRun) {
        Write-Output 'Dry-run complete; no files changed.'
        exit 0
    }

    Invoke-HarnessSyncPlan -Plan $plan
    Write-Output 'Sync applied successfully.'
    exit 0
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}
