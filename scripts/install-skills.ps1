[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$CodexSkillsRoot,
    [string[]]$Name = @('repo-research', 'github-operations', 'self-improvement', 'long-running-work'),
    [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$ManifestPath
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

    if (Test-Path -LiteralPath $resolvedManifestPath -PathType Leaf) {
        throw "Refusing to overwrite existing harness manifest: $resolvedManifestPath. Use sync-skills.ps1 for updates."
    }

    $sourceRoot = Resolve-HarnessDirectory -Path (Join-Path $resolvedRepositoryRoot 'skills')
    $requestedNames = Get-HarnessSkillNames -SourceRoot $sourceRoot -Name $Name
    $existing = @($requestedNames | Where-Object { Test-Path -LiteralPath (Join-Path $resolvedSkillsRoot $_) })
    if ($existing.Count -gt 0) {
        throw "Refusing to overwrite existing skill directories: $($existing -join ', '). Use sync-skills.ps1 for updates."
    }

    $plan = Get-HarnessSyncPlan -RepositoryRoot $resolvedRepositoryRoot -CodexSkillsRoot $resolvedSkillsRoot -ManifestPath $resolvedManifestPath -Name $requestedNames
    if ($plan.conflicts.Count -gt 0) {
        Write-HarnessSyncPlan -Plan $plan
        throw 'Initial install cannot continue because one or more managed paths conflict.'
    }

    Invoke-HarnessSyncPlan -Plan $plan
    foreach ($skillName in $requestedNames) {
        Write-Output "Installed skill: $skillName"
    }
    Write-Output "Wrote harness manifest: $resolvedManifestPath"
    exit 0
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}
