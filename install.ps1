<#
.SYNOPSIS  AUTO-BUILDER installer for Windows PowerShell 5.1+ and PowerShell 7.
.DESCRIPTION
  Installs the skill and subagents without overwriting existing files.
    .\install.ps1 -Personal             -> %USERPROFILE%\.claude\...
    .\install.ps1 -Project [-Path DIR]  -> DIR\.claude\... (default: current directory)
  -DryRun shows actions only. -Update replaces differing package files (old file kept
  as .bak, .bak.1, ...). Symlinks/junctions at install locations are never replaced.
  Files left from older versions are reported as STALE, never deleted.
  Behaviour mirrors install.sh. NOTE: this script has not been executed by the author
  (no PowerShell available during development) - please report problems.
#>
[CmdletBinding()]
param(
  [switch]$Personal,
  [switch]$Project,
  [string]$Path,
  [switch]$DryRun,
  [switch]$Update
)
$ErrorActionPreference = 'Stop'
function Fail([string]$m) { [Console]::Error.WriteLine("error: $m"); exit 1 }

if ($Personal.IsPresent -eq $Project.IsPresent) { Fail 'Choose exactly one of -Personal or -Project.' }
if ($Personal.IsPresent -and $PSBoundParameters.ContainsKey('Path')) { Fail '-Path only applies to -Project.' }

$srcRoot   = $PSScriptRoot
$srcSkill  = Join-Path $srcRoot '.claude/skills/auto-builder'
$srcAgents = Join-Path $srcRoot '.claude/agents'
if (-not (Test-Path -LiteralPath (Join-Path $srcSkill 'SKILL.md'))) { Fail "Missing $srcSkill\SKILL.md (run from a complete checkout)." }
if (-not (Get-ChildItem -LiteralPath $srcAgents -Filter *.md -ErrorAction SilentlyContinue)) { Fail "No agent files in $srcAgents." }

if ($Personal.IsPresent) {
  $home_ = $env:USERPROFILE; if (-not $home_) { $home_ = $HOME }
  if (-not $home_) { Fail 'Cannot determine home directory.' }
  $parent = $home_
} else {
  if (-not $PSBoundParameters.ContainsKey('Path')) { $Path = (Get-Location).Path }
  if (-not (Test-Path -LiteralPath $Path -PathType Container)) { Fail "Project directory does not exist: $Path" }
  $parent = (Resolve-Path -LiteralPath $Path).Path
}
$base = Join-Path $parent '.claude'
$baseResolved = if (Test-Path -LiteralPath $base) { (Resolve-Path -LiteralPath $base).Path } else { $base }
if ([IO.Path]::GetFullPath($baseResolved).TrimEnd('\','/') -ieq [IO.Path]::GetFullPath((Join-Path $srcRoot '.claude')).TrimEnd('\','/')) {
  Fail 'Target is this repository itself; pick another project or -Personal.'
}

$dstSkill  = Join-Path $base 'skills/auto-builder'
$dstAgents = Join-Path $base 'agents'
$n = @{ Installed = 0; Updated = 0; Unchanged = 0; Preserved = 0; Conflicts = 0; Stale = 0 }

if (-not $DryRun) {
  try { New-Item -ItemType Directory -Force -Path $dstSkill, $dstAgents | Out-Null }
  catch { Fail "Cannot create $base (check permissions): $($_.Exception.Message)" }
}

function Get-IsLink($p) { $i = Get-Item -LiteralPath $p -Force; return [bool]($i.Attributes -band [IO.FileAttributes]::ReparsePoint) }
function Next-Backup($t) { $b = "$t.bak"; $i = 1; while (Test-Path -LiteralPath $b) { $b = "$t.bak.$i"; $i++ }; return $b }

function Install-One($s, $t) {
  if ((Test-Path -LiteralPath $t) -and (Get-IsLink $t)) {
    Write-Host "CONFLICT  $t is a symlink/junction; left untouched"; $script:n.Conflicts++
  } elseif (Test-Path -LiteralPath $t -PathType Container) {
    Write-Host "CONFLICT  $t is a directory, expected a file; left untouched"; $script:n.Conflicts++
  } elseif (-not (Test-Path -LiteralPath $t)) {
    Write-Host "INSTALL   $t"
    if (-not $DryRun) { New-Item -ItemType Directory -Force -Path (Split-Path $t) | Out-Null; Copy-Item -LiteralPath $s -Destination $t }
    $script:n.Installed++
  } elseif ((Get-FileHash -LiteralPath $s).Hash -eq (Get-FileHash -LiteralPath $t).Hash) {
    $script:n.Unchanged++
  } elseif ($Update) {
    $bak = Next-Backup $t
    Write-Host "UPDATE    $t (backup: $bak)"
    if (-not $DryRun) { Copy-Item -LiteralPath $t -Destination $bak; Copy-Item -LiteralPath $s -Destination $t -Force }
    $script:n.Updated++
  } else {
    Write-Host "PRESERVE  $t (differs; kept your version, use -Update to replace)"
    $script:n.Preserved++
  }
}

Write-Host "OS: Windows | mode: $(if ($Personal.IsPresent) {'personal'} else {'project'}) | target: $base$(if ($DryRun) { ' | DRY RUN' })"
$srcSkillFull = (Resolve-Path -LiteralPath $srcSkill).Path
$shipped = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
Get-ChildItem -LiteralPath $srcSkill -Recurse -File |
  Where-Object { $_.Name -ne '.DS_Store' -and $_.Name -notlike '*.bak' -and $_.Name -notlike '*.bak.*' } |
  Sort-Object FullName | ForEach-Object {
    $rel = $_.FullName.Substring($srcSkillFull.Length).TrimStart('\','/').Replace('\','/')
    [void]$shipped.Add($rel)
    Install-One $_.FullName (Join-Path $dstSkill $rel)
  }
Get-ChildItem -LiteralPath $srcAgents -Filter *.md | ForEach-Object { Install-One $_.FullName (Join-Path $dstAgents $_.Name) }

if (Test-Path -LiteralPath $dstSkill) {
  $dstFull = (Resolve-Path -LiteralPath $dstSkill).Path
  Get-ChildItem -LiteralPath $dstSkill -Recurse -File | Sort-Object FullName | ForEach-Object {
    $rel = $_.FullName.Substring($dstFull.Length).TrimStart('\','/').Replace('\','/')
    if ($rel -like '*.bak' -or $rel -like '*.bak.*') { return }
    if (-not $shipped.Contains($rel)) {
      Write-Host "STALE     $($_.FullName) (not part of this version; remove manually if unused)"; $script:n.Stale++
    }
  }
}

Write-Host ''
Write-Host ("Installed: {0} | updated: {1} | unchanged: {2} | preserved: {3} | conflicts: {4} | stale: {5}" -f $n.Installed, $n.Updated, $n.Unchanged, $n.Preserved, $n.Conflicts, $n.Stale)
if ($DryRun) { Write-Host 'Dry run: nothing was written.' }
if ($n.Preserved -gt 0) { Write-Host "Note: $($n.Preserved) file(s) differ from this version, so your install may mix versions. Run with -Update to sync." }
Write-Host "Skill:  $dstSkill"
Write-Host "Agents: $dstAgents"
Write-Host 'Next: open Claude Code in your project and run /auto-builder <your goal>'
Write-Host 'Note: the optional helper/hook scripts are bash; use Git Bash or WSL to run them.'
if ($n.Conflicts -gt 0) { exit 1 }
