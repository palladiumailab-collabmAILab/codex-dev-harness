Set-StrictMode -Version Latest

function Resolve-HarnessAbsolutePath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [switch]$MustExist
    )

    if ([System.IO.Path]::IsPathRooted($Path)) {
        $candidate = $Path
    }
    else {
        $candidate = Join-Path (Get-Location).Path $Path
    }

    $resolved = [System.IO.Path]::GetFullPath($candidate)
    if ($MustExist -and -not (Test-Path -LiteralPath $resolved)) {
        throw "Path was not found: $resolved"
    }

    return $resolved
}

function Resolve-HarnessDirectory {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [switch]$Create
    )

    $resolved = Resolve-HarnessAbsolutePath -Path $Path
    if (-not (Test-Path -LiteralPath $resolved -PathType Container)) {
        if (-not $Create) {
            throw "Directory was not found: $resolved"
        }
        New-Item -ItemType Directory -Path $resolved -Force | Out-Null
    }

    return (Resolve-Path -LiteralPath $resolved).Path.TrimEnd('\', '/')
}

function Resolve-HarnessManifestPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ManifestPath
    )

    return Resolve-HarnessAbsolutePath -Path $ManifestPath
}

function Resolve-HarnessRelativePath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Root,
        [Parameter(Mandatory = $true)]
        [string]$RelativePath
    )

    $normalized = ($RelativePath -replace '\\', '/')
    if ([string]::IsNullOrWhiteSpace($normalized)) {
        throw 'A managed file path cannot be empty.'
    }
    if ([System.IO.Path]::IsPathRooted($normalized) -or $normalized -match '(^|/)\.\.?(/|$)') {
        throw "Managed file path must stay below the skills root: $RelativePath"
    }

    $child = $normalized -replace '/', [System.IO.Path]::DirectorySeparatorChar
    $candidate = [System.IO.Path]::GetFullPath((Join-Path -Path $Root -ChildPath $child))
    $rootWithSeparator = $Root.TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
    if (-not $candidate.StartsWith($rootWithSeparator, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Managed file path escaped the skills root: $RelativePath"
    }

    return $candidate
}

function Test-HarnessPathOverlap {
    param(
        [Parameter(Mandatory = $true)]
        [string]$First,
        [Parameter(Mandatory = $true)]
        [string]$Second
    )

    $firstRoot = $First.TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
    $secondRoot = $Second.TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
    return $First.Equals($Second, [System.StringComparison]::OrdinalIgnoreCase) -or
        $First.StartsWith($secondRoot, [System.StringComparison]::OrdinalIgnoreCase) -or
        $Second.StartsWith($firstRoot, [System.StringComparison]::OrdinalIgnoreCase)
}

function Invoke-HarnessGitText {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RepositoryRoot,
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,
        [Parameter(Mandatory = $true)]
        [string]$Description
    )

    $output = & git -C $RepositoryRoot @Arguments 2>$null
    $exitCode = $LASTEXITCODE
    $text = ($output -join "`n").Trim()
    if ($exitCode -ne 0 -or [string]::IsNullOrWhiteSpace($text)) {
        throw "Unable to read $Description from git repository: $RepositoryRoot"
    }

    return $text
}

function Get-HarnessSourceRepository {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RemoteUrl
    )

    if ($RemoteUrl -match 'github\.com[:/](?<repository>[^/]+/[^/]+?)(?:\.git)?$') {
        return "https://github.com/$($Matches.repository)"
    }

    return ($RemoteUrl -replace '(https?://)[^/@]+@', '$1')
}

function Get-HarnessSourceInfo {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RepositoryRoot
    )

    $commit = Invoke-HarnessGitText -RepositoryRoot $RepositoryRoot -Arguments @('rev-parse', '--verify', 'HEAD') -Description 'source commit'
    $remote = Invoke-HarnessGitText -RepositoryRoot $RepositoryRoot -Arguments @('config', '--get', 'remote.origin.url') -Description 'source repository'
    $version = Invoke-HarnessGitText -RepositoryRoot $RepositoryRoot -Arguments @('describe', '--tags', '--always', 'HEAD') -Description 'source version'

    return [pscustomobject]@{
        source_repository = Get-HarnessSourceRepository -RemoteUrl $remote
        source_commit = $commit
        source_version = $version
    }
}

function Get-HarnessFileHash {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Cannot hash missing file: $Path"
    }

    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-HarnessSkillNames {
    param(
        [Parameter(Mandatory = $true)]
        [string]$SourceRoot,
        [Parameter(Mandatory = $true)]
        [string[]]$Name
    )

    $requestedNames = @(
        $Name |
            ForEach-Object { $_ -split ',' } |
            ForEach-Object { $_.Trim() } |
            Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
            Sort-Object -Unique
    )
    if ($requestedNames.Count -eq 0) {
        throw 'At least one skill name must be specified.'
    }

    $availableNames = @(Get-ChildItem -LiteralPath $SourceRoot -Directory | Select-Object -ExpandProperty Name)
    $missing = @($requestedNames | Where-Object { $_ -notin $availableNames })
    if ($missing.Count -gt 0) {
        throw "Unknown skill name(s): $($missing -join ', ')"
    }

    return $requestedNames
}

function Get-HarnessSourceFiles {
    param(
        [Parameter(Mandatory = $true)]
        [string]$SourceRoot,
        [Parameter(Mandatory = $true)]
        [string[]]$Name
    )

    $records = @()
    foreach ($skillName in $Name) {
        $skillRoot = Join-Path $SourceRoot $skillName
        $files = @(Get-ChildItem -LiteralPath $skillRoot -File -Recurse | Sort-Object FullName)
        foreach ($file in $files) {
            $relativePath = $file.FullName.Substring($SourceRoot.Length).TrimStart('\', '/') -replace '\\', '/'
            $records += [pscustomobject]@{
                path = $relativePath
                sha256 = Get-HarnessFileHash -Path $file.FullName
            }
        }
    }

    if ($records.Count -eq 0) {
        throw "No managed files were found for skill(s): $($Name -join ', ')"
    }

    return @($records | Sort-Object path)
}

function Read-HarnessManifest {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ManifestPath
    )

    if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
        return $null
    }

    try {
        return (Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json)
    }
    catch {
        throw "Unable to parse harness manifest: $ManifestPath. $($_.Exception.Message)"
    }
}

function Get-HarnessManifestRecords {
    param(
        [Parameter(Mandatory = $false)]
        [AllowNull()]
        [psobject]$Manifest
    )

    if ($null -eq $Manifest) {
        return @()
    }
    if ($Manifest.schema_version -ne 1) {
        throw "Unsupported harness manifest schema version: $($Manifest.schema_version)"
    }
    if ($Manifest.managed_root -ne 'skills') {
        throw "Unsupported harness managed root: $($Manifest.managed_root)"
    }
    if ([string]::IsNullOrWhiteSpace([string]$Manifest.source_repository) -or
        [string]::IsNullOrWhiteSpace([string]$Manifest.source_commit) -or
        [string]::IsNullOrWhiteSpace([string]$Manifest.source_version)) {
        throw 'Harness manifest is missing source repository, commit, or version.'
    }

    $records = @()
    $seen = @{}
    foreach ($record in @($Manifest.managed_files)) {
        if ($null -eq $record -or [string]::IsNullOrWhiteSpace([string]$record.path)) {
            throw 'Harness manifest contains an invalid managed file record.'
        }
        $path = ([string]$record.path -replace '\\', '/')
        $hash = ([string]$record.sha256).ToLowerInvariant()
        if ($seen.ContainsKey($path)) {
            throw "Harness manifest contains duplicate managed file: $path"
        }
        if ($hash -notmatch '^[0-9a-f]{64}$') {
            throw "Harness manifest contains an invalid SHA-256 for: $path"
        }
        $seen[$path] = $true
        $records += [pscustomobject]@{ path = $path; sha256 = $hash }
    }

    return @($records | Sort-Object path)
}

function Test-HarnessSelectedPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string[]]$Name
    )

    $skillName = ($Path -split '/')[0]
    return $skillName -in $Name
}

function Compare-HarnessRecords {
    param(
        [Parameter(Mandatory = $true)]
        [object[]]$First,
        [Parameter(Mandatory = $true)]
        [object[]]$Second
    )

    $firstJson = (@($First | Sort-Object path | ForEach-Object { [ordered]@{ path = $_.path; sha256 = $_.sha256 } }) | ConvertTo-Json -Depth 4 -Compress)
    $secondJson = (@($Second | Sort-Object path | ForEach-Object { [ordered]@{ path = $_.path; sha256 = $_.sha256 } }) | ConvertTo-Json -Depth 4 -Compress)
    return $firstJson -eq $secondJson
}

function Get-HarnessSyncPlan {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RepositoryRoot,
        [Parameter(Mandatory = $true)]
        [string]$CodexSkillsRoot,
        [Parameter(Mandatory = $true)]
        [string]$ManifestPath,
        [Parameter(Mandatory = $true)]
        [string[]]$Name
    )

    $resolvedRepositoryRoot = Resolve-HarnessDirectory -Path $RepositoryRoot
    $resolvedSkillsRoot = Resolve-HarnessDirectory -Path $CodexSkillsRoot -Create
    $resolvedManifestPath = Resolve-HarnessManifestPath -ManifestPath $ManifestPath
    $sourceRoot = Resolve-HarnessDirectory -Path (Join-Path $resolvedRepositoryRoot 'skills')

    if (Test-HarnessPathOverlap -First $resolvedSkillsRoot -Second $sourceRoot) {
        throw 'The destination skills root must not overlap the source skills root.'
    }

    $selectedNames = Get-HarnessSkillNames -SourceRoot $sourceRoot -Name $Name
    $sourceInfo = Get-HarnessSourceInfo -RepositoryRoot $resolvedRepositoryRoot
    $sourceRecords = @(Get-HarnessSourceFiles -SourceRoot $sourceRoot -Name $selectedNames)
    $previousManifest = Read-HarnessManifest -ManifestPath $resolvedManifestPath
    $previousRecords = @(Get-HarnessManifestRecords -Manifest $previousManifest)

    $sourceByPath = @{}
    foreach ($record in $sourceRecords) {
        $sourceByPath[$record.path] = $record
    }

    $previousByPath = @{}
    foreach ($record in $previousRecords) {
        if (Test-HarnessSelectedPath -Path $record.path -Name $selectedNames) {
            $previousByPath[$record.path] = $record
        }
    }

    $paths = @($sourceByPath.Keys + $previousByPath.Keys | Sort-Object -Unique)
    $operations = @()
    foreach ($path in $paths) {
        $destinationPath = Resolve-HarnessRelativePath -Root $resolvedSkillsRoot -RelativePath $path
        $sourceRecord = $null
        $previousRecord = $null
        if ($sourceByPath.ContainsKey($path)) {
            $sourceRecord = $sourceByPath[$path]
        }
        if ($previousByPath.ContainsKey($path)) {
            $previousRecord = $previousByPath[$path]
        }

        if ($null -ne $sourceRecord) {
            if (-not (Test-Path -LiteralPath $destinationPath)) {
                $operations += [pscustomobject]@{ action = 'add'; path = $path; source_path = (Join-Path $sourceRoot ($path -replace '/', [System.IO.Path]::DirectorySeparatorChar)); destination_path = $destinationPath; reason = 'destination missing' }
                continue
            }
            if (-not (Test-Path -LiteralPath $destinationPath -PathType Leaf)) {
                $operations += [pscustomobject]@{ action = 'conflict'; path = $path; source_path = $null; destination_path = $destinationPath; reason = 'destination path exists but is not a file' }
                continue
            }

            $destinationHash = Get-HarnessFileHash -Path $destinationPath
            if ($destinationHash -eq $sourceRecord.sha256) {
                $operations += [pscustomobject]@{ action = 'unchanged'; path = $path; source_path = $null; destination_path = $destinationPath; reason = 'content already matches source' }
            }
            elseif ($null -ne $previousRecord -and $destinationHash -eq $previousRecord.sha256) {
                $operations += [pscustomobject]@{ action = 'update'; path = $path; source_path = (Join-Path $sourceRoot ($path -replace '/', [System.IO.Path]::DirectorySeparatorChar)); destination_path = $destinationPath; reason = 'destination matches previous managed hash' }
            }
            else {
                $operations += [pscustomobject]@{ action = 'conflict'; path = $path; source_path = $null; destination_path = $destinationPath; reason = 'destination differs from both source and recorded previous hash' }
            }
        }
        elseif (Test-Path -LiteralPath $destinationPath) {
            if (-not (Test-Path -LiteralPath $destinationPath -PathType Leaf)) {
                $operations += [pscustomobject]@{ action = 'conflict'; path = $path; source_path = $null; destination_path = $destinationPath; reason = 'stale managed path exists but is not a file' }
                continue
            }
            $destinationHash = Get-HarnessFileHash -Path $destinationPath
            if ($null -ne $previousRecord -and $destinationHash -eq $previousRecord.sha256) {
                $operations += [pscustomobject]@{ action = 'remove'; path = $path; source_path = $null; destination_path = $destinationPath; reason = 'managed source file no longer exists' }
            }
            else {
                $operations += [pscustomobject]@{ action = 'conflict'; path = $path; source_path = $null; destination_path = $destinationPath; reason = 'stale managed file was modified or has no provenance record' }
            }
        }
    }

    $outsideSelected = @($previousRecords | Where-Object { -not (Test-HarnessSelectedPath -Path $_.path -Name $selectedNames) })
    $finalRecords = @($outsideSelected + $sourceRecords | Sort-Object path)
    $manifestNeedsUpdate = $null -eq $previousManifest -or
        $previousManifest.source_repository -ne $sourceInfo.source_repository -or
        $previousManifest.source_commit -ne $sourceInfo.source_commit -or
        $previousManifest.source_version -ne $sourceInfo.source_version -or
        -not (Compare-HarnessRecords -First $previousRecords -Second (@($outsideSelected + $sourceRecords)))

    return [pscustomobject]@{
        repository_root = $resolvedRepositoryRoot
        skills_root = $resolvedSkillsRoot
        source_root = $sourceRoot
        manifest_path = $resolvedManifestPath
        selected_names = $selectedNames
        source_info = $sourceInfo
        source_records = $sourceRecords
        previous_records = $previousRecords
        final_records = $finalRecords
        operations = @($operations | Sort-Object path, action)
        conflicts = @($operations | Where-Object { $_.action -eq 'conflict' })
        manifest_needs_update = $manifestNeedsUpdate
    }
}

function Write-HarnessSyncPlan {
    param(
        [Parameter(Mandatory = $true)]
        [psobject]$Plan
    )

    Write-Output "Source: $($Plan.source_info.source_repository)@$($Plan.source_info.source_commit)"
    foreach ($operation in @($Plan.operations)) {
        if ($operation.action -eq 'conflict') {
            Write-Output ("{0}: {1} ({2})" -f $operation.action, $operation.path, $operation.reason)
        }
        else {
            Write-Output ("{0}: {1}" -f $operation.action, $operation.path)
        }
    }

    $counts = @{}
    foreach ($action in @('add', 'update', 'unchanged', 'remove', 'conflict')) {
        $counts[$action] = @($Plan.operations | Where-Object { $_.action -eq $action }).Count
    }
    Write-Output ("Summary: add={0} update={1} unchanged={2} remove={3} conflict={4}" -f $counts.add, $counts.update, $counts.unchanged, $counts.remove, $counts.conflict)
    if ($Plan.manifest_needs_update) {
        Write-Output 'Manifest: update required'
    }
    else {
        Write-Output 'Manifest: unchanged'
    }
}

function Write-HarnessManifest {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ManifestPath,
        [Parameter(Mandatory = $true)]
        [psobject]$SourceInfo,
        [Parameter(Mandatory = $true)]
        [object[]]$ManagedFiles
    )

    $manifestDirectory = Split-Path -Parent $ManifestPath
    if (-not [string]::IsNullOrWhiteSpace($manifestDirectory)) {
        New-Item -ItemType Directory -Path $manifestDirectory -Force | Out-Null
    }

    $manifest = [ordered]@{
        schema_version = 1
        source_repository = $SourceInfo.source_repository
        source_commit = $SourceInfo.source_commit
        source_version = $SourceInfo.source_version
        managed_root = 'skills'
        managed_files = @(@($ManagedFiles | Sort-Object path | ForEach-Object {
            [ordered]@{
                path = $_.path
                sha256 = $_.sha256
            }
        }))
    }
    $json = $manifest | ConvertTo-Json -Depth 8
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($ManifestPath, $json, $utf8)
}

function Invoke-HarnessSyncPlan {
    param(
        [Parameter(Mandatory = $true)]
        [psobject]$Plan
    )

    foreach ($operation in @($Plan.operations | Where-Object { $_.action -in @('add', 'update') })) {
        $parent = Split-Path -Parent $operation.destination_path
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
        Copy-Item -LiteralPath $operation.source_path -Destination $operation.destination_path -Force
    }
    foreach ($operation in @($Plan.operations | Where-Object { $_.action -eq 'remove' })) {
        Remove-Item -LiteralPath $operation.destination_path -Force
    }
    if ($Plan.manifest_needs_update) {
        Write-HarnessManifest -ManifestPath $Plan.manifest_path -SourceInfo $Plan.source_info -ManagedFiles $Plan.final_records
    }
}

function Test-HarnessManifest {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ManifestPath,
        [Parameter(Mandatory = $true)]
        [string]$CodexSkillsRoot
    )

    $errors = @()
    if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
        return @("Harness manifest was not found: $ManifestPath")
    }

    try {
        $skillsRoot = Resolve-HarnessDirectory -Path $CodexSkillsRoot
        $manifest = Read-HarnessManifest -ManifestPath $ManifestPath
        $records = @(Get-HarnessManifestRecords -Manifest $manifest)
        foreach ($record in $records) {
            $path = Resolve-HarnessRelativePath -Root $skillsRoot -RelativePath $record.path
            if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
                $errors += "Managed file is missing: $($record.path)"
                continue
            }
            $actualHash = Get-HarnessFileHash -Path $path
            if ($actualHash -ne $record.sha256) {
                $errors += "Managed file hash drifted: $($record.path) (expected $($record.sha256), found $actualHash)"
            }
        }
    }
    catch {
        $errors += $_.Exception.Message
    }

    return @($errors)
}
