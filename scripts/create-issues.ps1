<#
.SYNOPSIS
Creates Bracketeer's GitHub issues from the user stories.

.DESCRIPTION
Reads docs/requirements/user-stories.md and creates one issue per Must or Could
story (with its acceptance criteria as a checklist), plus the task issues listed
in $Tasks below. Each issue is added to the project board with Status = Backlog,
and each story also gets its Priority.

Without -Create, the script only prints what it would do (a dry run).
Issues whose title already exists are skipped, so it is safe to run again.

.EXAMPLE
.\scripts\create-issues.ps1           # dry run
.\scripts\create-issues.ps1 -Create   # create the issues
#>
param(
    [switch]$Create
)

$ErrorActionPreference = 'Stop'

$Owner = 'ajlight89'
$Repo = 'ajlight89/bracketeer'
$ProjectNumber = 5
$StoriesFile = Join-Path $PSScriptRoot '..\docs\requirements\user-stories.md'
$StoriesUrl = "https://github.com/$Repo/blob/main/docs/requirements/user-stories.md"

# Task issues: the work that builds the stories. Stories lists the story IDs
# each task contributes to.
$Tasks = @(
    @{ Title = 'Write the design docs'; Milestone = 'Domain complete'; Stories = @()
       Body = 'Write `docs/design.md` (UML class diagram, layers, design patterns, save format) and `docs/key-decisions.md` (key decisions and scope changes).' }
    @{ Title = 'Domain: value objects and the Match and Round entities'; Milestone = 'Domain complete'; Stories = @('US-07')
       Body = 'Player names, results (played or forfeit), match points, and the Match and Round classes, with unit and property tests.' }
    @{ Title = 'Domain: players and seeding'; Milestone = 'Domain complete'; Stories = @('US-01', 'US-02', 'US-03')
       Body = 'Register, edit, remove, and rename players on a Tournament, and seed them manually, randomly, or by rating.' }
    @{ Title = 'Domain: format interface, round robin, and starting a tournament'; Milestone = 'Domain complete'; Stories = @('US-05')
       Body = 'The TournamentFormat interface (Strategy pattern), the round robin schedule (circle method), and Tournament.start().' }
    @{ Title = 'Domain: record and clear results, including forfeits'; Milestone = 'Domain complete'; Stories = @('US-07')
       Body = 'Record and clear a match result, record a forfeit, and reject draws in formats that need a winner.' }
    @{ Title = 'Domain: round robin standings'; Milestone = 'Domain complete'; Stories = @('US-09')
       Body = 'Standings for round robin: match points, then game differential, then seed, with matches played, wins, draws, and losses.' }
    @{ Title = 'Domain: single elimination'; Milestone = 'Domain complete'; Stories = @('US-04', 'US-09')
       Body = 'The single elimination format, generating the next round, locking earlier results, completion, and placement standings.' }
    @{ Title = 'Domain: format registry and restoring a saved tournament'; Milestone = 'Domain complete'; Stories = @('US-10')
       Body = 'Look up a format by its key, and rebuild a started tournament from saved data.' }
    @{ Title = 'Save and open tournaments as JSON files'; Milestone = 'Working app'; Stories = @('US-10')
       Body = 'A TournamentRepository that saves and loads tournaments as JSON, validates files on load, and never leaves a half-written file. Includes round-trip tests.' }
    @{ Title = 'GUI: Players, Matches, and Standings tabs and the File menu'; Milestone = 'Working app'; Stories = @('US-01', 'US-02', 'US-03', 'US-04', 'US-05', 'US-07', 'US-09', 'US-10')
       Body = 'The Tkinter window: Players, Matches, and Standings tabs, dialogs, the File menu (New, Open, Save, Save As), and clear error messages.' }
    @{ Title = 'Package Bracketeer as a single .exe'; Milestone = 'Working app'; Stories = @('US-12')
       Body = 'Build a single-file Windows executable with PyInstaller and test it on a computer without Python.' }
    @{ Title = 'Demo data script and manual test checklist'; Milestone = 'Working app'; Stories = @()
       Body = 'A script that creates sample tournaments for the demo, and a checklist for the requirements that are checked by hand.' }
    @{ Title = 'Write the report'; Milestone = 'Delivery'; Stories = @()
       Body = 'The project report (10 pages or less).' }
    @{ Title = 'Prepare the presentation and demo'; Milestone = 'Delivery'; Stories = @()
       Body = 'The slides, a rehearsed live demo, and a recorded backup of the demo.' }
    @{ Title = 'Prepare the submission'; Milestone = 'Delivery'; Stories = @()
       Body = 'Make the repository public with the v1.0.0 release, and build the submission zip.' }
)

function Invoke-Gh {
    # Runs gh and stops on failure. External programs report failure through
    # $LASTEXITCODE, which $ErrorActionPreference does not check.
    $output = & gh @args
    if ($LASTEXITCODE -ne 0) {
        throw "gh $($args -join ' ') failed with exit code $LASTEXITCODE"
    }
    return $output
}

function ConvertFrom-GhJson {
    param([Parameter(ValueFromPipeline)]$Lines)
    begin { $all = @() }
    process { $all += $Lines }
    end { return ($all -join "`n") | ConvertFrom-Json }
}

function Get-Stories {
    $stories = @()
    $current = $null
    foreach ($line in Get-Content -Path $StoriesFile -Encoding utf8) {
        if ($line -match '^## (US-\d{2}): (.+)$') {
            if ($current) { $stories += [pscustomobject]$current }
            $current = @{ Id = $Matches[1]; Name = $Matches[2]; Priority = ''; Story = ''; Criteria = @() }
        }
        elseif ($line -match '^## ') {
            if ($current) { $stories += [pscustomobject]$current }
            $current = $null
        }
        elseif ($current) {
            if ($line -match '^\*\*Priority:\*\* (\S+)') { $current.Priority = $Matches[1] }
            elseif ($line -match '^As an? ') { $current.Story = $line }
            elseif ($line -match '^\d+\. (.+)$') { $current.Criteria += $Matches[1] }
        }
    }
    if ($current) { $stories += [pscustomobject]$current }
    return $stories
}

function Get-Anchor {
    # GitHub's heading anchors: lower case, punctuation removed, spaces as hyphens.
    param([string]$Heading)
    return (($Heading.ToLower() -replace '[^a-z0-9 -]', '') -replace ' ', '-')
}

function New-TrackedIssue {
    param(
        [string]$Title,
        [string]$Body,
        [string]$Label,
        [string]$Milestone,
        [string]$Priority = ''
    )
    if ($script:Existing.ContainsKey($Title)) {
        Write-Host "skip     #$($script:Existing[$Title]) $Title (already exists)"
        return $script:Existing[$Title]
    }
    if (-not $Create) {
        Write-Host "would create [$Label | $Milestone | $Priority] $Title"
        return 0
    }

    $bodyFile = New-TemporaryFile
    try {
        Set-Content -Path $bodyFile -Value $Body -Encoding utf8NoBOM
        $url = Invoke-Gh issue create --repo $Repo --title $Title --body-file $bodyFile.FullName --label $Label --milestone $Milestone
    }
    finally {
        Remove-Item $bodyFile
    }
    $url = ($url | Select-Object -Last 1).Trim()
    $number = [int]($url -split '/')[-1]

    $itemId = (Invoke-Gh project item-add $ProjectNumber --owner $Owner --url $url --format json --jq '.id' | Select-Object -Last 1).Trim()
    if (-not $itemId) { throw "No board item ID returned for $url" }
    Invoke-Gh project item-edit --id $itemId --project-id $script:ProjectId --field-id $script:StatusField.id --single-select-option-id $script:BacklogId | Out-Null

    if ($Priority) {
        $optionId = ($script:PriorityField.options | Where-Object name -eq $Priority).id
        if (-not $optionId) { throw "The Priority field has no option named '$Priority'" }
        Invoke-Gh project item-edit --id $itemId --project-id $script:ProjectId --field-id $script:PriorityField.id --single-select-option-id $optionId | Out-Null
    }

    Write-Host "created  #$number $Title"
    $script:Existing[$Title] = $number
    return $number
}

# --- Look up what already exists ------------------------------------------------

$script:Existing = @{}
foreach ($issue in (Invoke-Gh issue list --repo $Repo --state all --limit 500 --json 'number,title' | ConvertFrom-GhJson)) {
    $script:Existing[$issue.title] = $issue.number
}

$script:ProjectId = (Invoke-Gh project view $ProjectNumber --owner $Owner --format json --jq '.id' | Select-Object -Last 1).Trim()
$fields = (Invoke-Gh project field-list $ProjectNumber --owner $Owner --format json | ConvertFrom-GhJson).fields
$script:StatusField = $fields | Where-Object name -eq 'Status'
$script:PriorityField = $fields | Where-Object name -eq 'Priority'
$script:BacklogId = ($script:StatusField.options | Where-Object name -eq 'Backlog').id
if (-not ($script:ProjectId -and $script:StatusField -and $script:PriorityField -and $script:BacklogId)) {
    throw 'The board is missing its ID, the Status field, the Priority field, or the Backlog option.'
}

if ($Create) { Write-Host "Creating issues in $Repo`n" } else { Write-Host "DRY RUN: nothing will be created. Add -Create to create the issues.`n" }

# --- Stories ------------------------------------------------------------------------

$storyNumbers = @{}
foreach ($story in Get-Stories) {
    if ($story.Priority -notin @('Must', 'Could')) { continue }
    if (-not $story.Story -or $story.Criteria.Count -eq 0) {
        throw "$($story.Id) is missing its story sentence or its acceptance criteria."
    }
    $title = "$($story.Id): $($story.Name)"
    $checklist = ($story.Criteria | ForEach-Object { "- [ ] $_" }) -join "`n"
    $body = @"
$($story.Story)

## Acceptance criteria

$checklist

Source: [$($story.Id) in user-stories.md]($StoriesUrl#$(Get-Anchor $title))
"@
    $storyNumbers[$story.Id] = New-TrackedIssue -Title $title -Body $body -Label 'story' -Milestone 'Working app' -Priority $story.Priority
}

# --- Tasks --------------------------------------------------------------------------

foreach ($task in $Tasks) {
    $body = $task.Body
    if ($task.Stories.Count -gt 0) {
        $links = $task.Stories | ForEach-Object {
            if ($storyNumbers[$_]) { "#$($storyNumbers[$_])" } else { $_ }
        }
        $body += "`n`nPart of: $($links -join ', ')"
    }
    New-TrackedIssue -Title $task.Title -Body $body -Label 'task' -Milestone $task.Milestone | Out-Null
}

Write-Host "`nDone."
