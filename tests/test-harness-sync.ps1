[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$repositoryRoot = (Resolve-Path -LiteralPath (Split-Path -Parent $PSScriptRoot)).Path
$syncScript = Join-Path $repositoryRoot 'scripts/sync-skills.ps1'
$installScript = Join-Path $repositoryRoot 'scripts/install-skills.ps1'
$validateScript = Join-Path $repositoryRoot 'scripts/validate-harness-manifest.ps1'
$testRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("codex-harness-sync-" + [guid]::NewGuid().ToString('N'))

function Assert-True {
    param(
        [Parameter(Mandatory = $true)]
        [bool]$Condition,
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    if (-not $Condition) {
        throw "Assertion failed: $Message"
    }
}

function Invoke-PwshScript {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ScriptPath,
        [string[]]$Arguments = @()
    )

    $output = & pwsh -NoProfile -NonInteractive -File $ScriptPath @Arguments 2>&1
    return [pscustomobject]@{
        exit_code = $LASTEXITCODE
        output = ($output -join "`n")
    }
}

function Invoke-Git {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    & git -C $Path @Arguments | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "git command failed in ${Path}: git $($Arguments -join ' ')"
    }
}

try {
    New-Item -ItemType Directory -Path $testRoot -Force | Out-Null
    $sourceRoot = Join-Path $testRoot 'source'
    $targetRoot = Join-Path $testRoot 'target'
    $skillsRoot = Join-Path $targetRoot '.codex/skills'
    $manifestPath = Join-Path $targetRoot 'harness.lock.json'
    New-Item -ItemType Directory -Path $sourceRoot -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $repositoryRoot 'skills') -Destination $sourceRoot -Recurse

    Invoke-Git -Path $sourceRoot -Arguments @('init', '-q')
    Invoke-Git -Path $sourceRoot -Arguments @('config', 'user.name', 'Harness Test')
    Invoke-Git -Path $sourceRoot -Arguments @('config', 'user.email', 'harness-test@example.invalid')
    Invoke-Git -Path $sourceRoot -Arguments @('remote', 'add', 'origin', 'https://github.com/example/codex-dev-harness.git')
    Invoke-Git -Path $sourceRoot -Arguments @('add', '--', 'skills')
    Invoke-Git -Path $sourceRoot -Arguments @('commit', '-qm', 'source revision one')

    $firstInstall = Invoke-PwshScript -ScriptPath $installScript -Arguments @(
        '-CodexSkillsRoot', $skillsRoot,
        '-ManifestPath', $manifestPath,
        '-RepositoryRoot', $sourceRoot,
        '-Name', 'repo-research,github-operations'
    )
    Assert-True ($firstInstall.exit_code -eq 0) "fresh install succeeded: $($firstInstall.output)"
    Assert-True (Test-Path -LiteralPath $manifestPath -PathType Leaf) 'fresh install wrote a manifest'

    $validate = Invoke-PwshScript -ScriptPath $validateScript -Arguments @(
        '-CodexSkillsRoot', $skillsRoot,
        '-ManifestPath', $manifestPath
    )
    Assert-True ($validate.exit_code -eq 0) "fresh manifest validates: $($validate.output)"

    $sameVersion = Invoke-PwshScript -ScriptPath $syncScript -Arguments @(
        '-CodexSkillsRoot', $skillsRoot,
        '-ManifestPath', $manifestPath,
        '-RepositoryRoot', $sourceRoot,
        '-Name', 'repo-research,github-operations',
        '-DryRun'
    )
    Assert-True ($sameVersion.exit_code -eq 0) "same-version dry-run succeeded: $($sameVersion.output)"
    Assert-True ($sameVersion.output -match 'unchanged=2') "same-version dry-run reports unchanged files: $($sameVersion.output)"

    $manifestBeforeNoOp = (Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash
    $sameVersionApply = Invoke-PwshScript -ScriptPath $syncScript -Arguments @(
        '-CodexSkillsRoot', $skillsRoot,
        '-ManifestPath', $manifestPath,
        '-RepositoryRoot', $sourceRoot,
        '-Name', 'repo-research,github-operations'
    )
    Assert-True ($sameVersionApply.exit_code -eq 0) "same-version sync succeeded: $($sameVersionApply.output)"
    Assert-True ((Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash -eq $manifestBeforeNoOp) 'same-version sync did not rewrite the manifest'

    $managedFile = Join-Path $sourceRoot 'skills/repo-research/SKILL.md'
    Add-Content -LiteralPath $managedFile -Value "`nUpgrade fixture revision two."
    Invoke-Git -Path $sourceRoot -Arguments @('add', '--', 'skills/repo-research/SKILL.md')
    Invoke-Git -Path $sourceRoot -Arguments @('commit', '-qm', 'source revision two')

    $unmanagedFile = Join-Path $skillsRoot 'repo-research/downstream-notes.txt'
    Set-Content -LiteralPath $unmanagedFile -Value 'preserve this file' -NoNewline
    $upgrade = Invoke-PwshScript -ScriptPath $syncScript -Arguments @(
        '-CodexSkillsRoot', $skillsRoot,
        '-ManifestPath', $manifestPath,
        '-RepositoryRoot', $sourceRoot,
        '-Name', 'repo-research,github-operations'
    )
    Assert-True ($upgrade.exit_code -eq 0) "old revision upgraded: $($upgrade.output)"
    Assert-True ((Get-Content -LiteralPath $managedFile -Raw) -match 'Upgrade fixture revision two') 'source fixture changed'
    Assert-True ((Get-Content -LiteralPath (Join-Path $skillsRoot 'repo-research/SKILL.md') -Raw) -match 'Upgrade fixture revision two') 'managed file upgraded'
    Assert-True ((Get-Content -LiteralPath $unmanagedFile -Raw) -eq 'preserve this file') 'unmanaged file survived sync'

    $drift = Invoke-PwshScript -ScriptPath $validateScript -Arguments @(
        '-CodexSkillsRoot', $skillsRoot,
        '-ManifestPath', $manifestPath
    )
    Assert-True ($drift.exit_code -eq 0) "post-upgrade manifest validates: $($drift.output)"

    $destinationManagedFile = Join-Path $skillsRoot 'repo-research/SKILL.md'
    Add-Content -LiteralPath $destinationManagedFile -Value "`nLocal modification that must not be overwritten."
    $beforeConflict = Get-Content -LiteralPath $destinationManagedFile -Raw
    $conflict = Invoke-PwshScript -ScriptPath $syncScript -Arguments @(
        '-CodexSkillsRoot', $skillsRoot,
        '-ManifestPath', $manifestPath,
        '-RepositoryRoot', $sourceRoot,
        '-Name', 'repo-research,github-operations',
        '-DryRun'
    )
    Assert-True ($conflict.exit_code -eq 2) "local modification returns conflict exit code: $($conflict.output)"
    Assert-True ($conflict.output -match 'conflict=1') "local modification is reported as conflict: $($conflict.output)"
    Assert-True ((Get-Content -LiteralPath $destinationManagedFile -Raw) -eq $beforeConflict) 'conflicting file was not overwritten'

    $manifestDrift = Join-Path $skillsRoot 'github-operations/SKILL.md'
    Add-Content -LiteralPath $manifestDrift -Value "`nTampered after sync."
    $driftValidation = Invoke-PwshScript -ScriptPath $validateScript -Arguments @(
        '-CodexSkillsRoot', $skillsRoot,
        '-ManifestPath', $manifestPath
    )
    Assert-True ($driftValidation.exit_code -eq 1) "tampering fails validation: $($driftValidation.output)"
    Assert-True ($driftValidation.output -match 'hash drifted') "tampering is identified as hash drift: $($driftValidation.output)"

    Write-Output 'Harness sync regression tests passed.'
    exit 0
}
finally {
    if (Test-Path -LiteralPath $testRoot) {
        Remove-Item -LiteralPath $testRoot -Recurse -Force
    }
}
