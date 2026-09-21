[CmdletBinding()]
param(
    [switch]$SkipDocker
)

Set-StrictMode -Version Latest
$repositoryRoot = (Resolve-Path -LiteralPath (Split-Path -Parent $PSScriptRoot)).Path

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Label,
        [Parameter(Mandatory = $true)]
        [scriptblock]$Command
    )

    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE."
    }
}

Push-Location $repositoryRoot
try {
    Invoke-Checked 'committed whitespace check' { git diff --check 4b825dc642cb6eb9a060e54bf8d69288fbee4904 HEAD }
    Invoke-Checked 'unstaged whitespace check' { git diff --check }
    Invoke-Checked 'staged whitespace check' { git diff --cached --check }
    Invoke-Checked 'pre-commit syntax check' { bash -n .githooks/pre-commit }
    Invoke-Checked 'pre-commit behavior tests' { bash tests/test-pre-commit.sh }
    Invoke-Checked 'harness sync regression tests' { pwsh -NoProfile -NonInteractive -File tests/test-harness-sync.ps1 }

    $hookEntry = (& git ls-files -s -- .githooks/pre-commit)
    if ($LASTEXITCODE -ne 0 -or -not $hookEntry) {
        throw 'Unable to inspect the tracked pre-commit hook.'
    }
    $hookMode = ($hookEntry -split '\s+')[0]
    if ($hookMode -ne '100755') {
        throw "Tracked pre-commit hook must be executable (100755); found $hookMode."
    }

    $instructionBudgets = @{
        'AGENTS.md' = 4096
        'templates/downstream/AGENTS.md' = 3072
        'profiles/astra/AGENTS.md' = 2048
        'profiles/sol-luna/AGENTS.md' = 2048
    }
    foreach ($relativePath in $instructionBudgets.Keys) {
        $size = (Get-Item -LiteralPath $relativePath).Length
        $budget = $instructionBudgets[$relativePath]
        if ($size -gt $budget) {
            throw "$relativePath exceeds the harness instruction budget: $size > $budget bytes."
        }
    }

    if ($SkipDocker) {
        Invoke-Checked 'Ruff lint' { python -m ruff check . }
        Invoke-Checked 'Ruff format check' { python -m ruff format --check . }
        Invoke-Checked 'skill validation' { python scripts/validate-skills.py skills }
        Invoke-Checked 'model profile validation' { python scripts/validate-model-profiles.py }
        Invoke-Checked 'schema-first validation' { python scripts/validate-schema-first.py --input tests/fixtures/schema-first/valid-model.json --check-generated }
        Invoke-Checked 'schema-first negative fixture validation' { python scripts/validate-schema-first.py --input tests/fixtures/schema-first/invalid-model.json --expect-invalid }
        Invoke-Checked 'architecture evaluation validation' { python scripts/validate-architecture-evals.py }
        Invoke-Checked 'contract unit tests' { python -m unittest discover -s tests -p 'test_*.py' }
        Invoke-Checked 'contract fixture validation' {
            python scripts/validate-contracts.py --fixture-root tests/fixtures/contracts/valid
            python scripts/validate-contracts.py --fixture-root tests/fixtures/contracts/invalid --expect-invalid
        }
    }
    else {
        Invoke-Checked 'Docker availability check' { docker info --format '{{.ServerVersion}}' }
        $mount = "type=bind,source=$repositoryRoot,target=/workspace,readonly"
        Invoke-Checked 'containerized harness validation' {
            docker run --rm --env RUFF_CACHE_DIR=/tmp/ruff-cache --mount $mount python:3.13-slim sh -c 'python -m pip install --root-user-action=ignore --disable-pip-version-check --no-cache-dir --quiet -r /workspace/requirements-dev.txt && cd /workspace && python -m ruff check . && python -m ruff format --check . && python scripts/validate-skills.py skills && python scripts/validate-model-profiles.py && python scripts/validate-schema-first.py --input tests/fixtures/schema-first/valid-model.json --check-generated && python scripts/validate-schema-first.py --input tests/fixtures/schema-first/invalid-model.json --expect-invalid && python scripts/validate-architecture-evals.py && python -m unittest discover -s tests -p "test_*.py" && python scripts/validate-contracts.py --fixture-root tests/fixtures/contracts/valid && python scripts/validate-contracts.py --fixture-root tests/fixtures/contracts/invalid --expect-invalid'
        }
    }

    Write-Output 'Harness validation passed.'
}
finally {
    Pop-Location
}
