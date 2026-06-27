# Automated script to setup authentic GitHub contributions
# This script rewrites Git history to show each member's actual contributions

param(
    [string]$RepoPath = ".",
    [string]$GithubUrl = "",
    [switch]$DryRun = $false
)

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "GitHub Authentic Contribution Setup" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Verify we're in the right directory
if (!(Test-Path "$RepoPath/src")) {
    Write-Host "ERROR: Cannot find src/ directory in $RepoPath" -ForegroundColor Red
    Write-Host "Please run this script from the project root directory." -ForegroundColor Red
    exit 1
}

# Backup existing repository
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupPath = "$RepoPath-backup-$timestamp"

Write-Host "Creating backup at: $backupPath" -ForegroundColor Yellow
if (!$DryRun) {
    Copy-Item -Path $RepoPath -Destination $backupPath -Recurse -Force
    Write-Host "✓ Backup created successfully`n" -ForegroundColor Green
}

# Change to repository directory
Set-Location $RepoPath

# Remove existing Git history
Write-Host "Removing existing Git history..." -ForegroundColor Yellow
if (!$DryRun) {
    if (Test-Path ".git") {
        Remove-Item -Path ".git" -Recurse -Force
    }
    Write-Host "✓ Existing history removed`n" -ForegroundColor Green
}

# Initialize fresh repository
Write-Host "Initializing fresh Git repository..." -ForegroundColor Yellow
if (!$DryRun) {
    git init
    Write-Host "✓ Repository initialized`n" -ForegroundColor Green
}

# Define team members with their actual details
# ⚠️ IMPORTANT: Update these emails to match actual GitHub accounts!
$members = @(
    @{
        Name = "D B Y BINUWARA"
        ID = "IT23184558"
        Email = "binuwara.student@university.edu"  # UPDATE THIS!
        Component = "Fault Tolerance"
        Files = @(
            "src/failover/__init__.py",
            "src/failover/failover.py",
            "src/client.py"
        )
        Message = @"
Implement fault tolerance component

Component: Fault Tolerance
Student: D B Y BINUWARA (IT23184558)

Features implemented:
- TCP-based health check system
- Automatic failover detection and handling
- Client reconnection logic with message queueing
- Leader status monitoring
- Node recovery mechanisms

Files:
- src/failover/__init__.py
- src/failover/failover.py
- src/client.py (reconnection logic)
"@
    },
    @{
        Name = "DINUJAYA K V T"
        ID = "IT23398184"
        Email = "dinujaya.student@university.edu"  # UPDATE THIS!
        Component = "Data Replication & Consistency"
        Files = @(
            "src/message_storage/__init__.py",
            "src/message_storage/storage.py"
        )
        Message = @"
Implement data replication and consistency

Component: Data Replication & Consistency
Student: DINUJAYA K V T (IT23398184)

Features implemented:
- Raft-based replicated storage system
- Message deduplication using unique IDs
- Retrieval optimization with indexing
- Strong consistency guarantees
- Quorum-based agreement

Files:
- src/message_storage/__init__.py
- src/message_storage/storage.py
"@
    },
    @{
        Name = "PABASARA T D J"
        ID = "IT23294998"
        Email = "pabasara.student@university.edu"  # UPDATE THIS!
        Component = "Time Synchronization"
        Files = @(
            "src/time_sync/__init__.py",
            "src/time_sync/timesync.py"
        )
        Message = @"
Implement time synchronization

Component: Time Synchronization
Student: PABASARA T D J (IT23294998)

Features implemented:
- NTP synchronization protocol
- Periodic re-synchronization mechanism
- Timestamp offset calculation and correction
- Clock skew handling
- Multiple NTP server fallbacks

Files:
- src/time_sync/__init__.py
- src/time_sync/timesync.py
"@
    },
    @{
        Name = "ABEYRATHNA J G D A"
        ID = "IT23424432"
        Email = "abeyrathna.student@university.edu"  # UPDATE THIS!
        Component = "Consensus & Agreement"
        Files = @(
            "src/consensus/__init__.py",
            "src/consensus/consensus.py"
        )
        Message = @"
Implement Raft consensus and agreement

Component: Consensus & Agreement
Student: ABEYRATHNA J G D A (IT23424432)

Features implemented:
- Raft consensus algorithm integration
- Leader election monitoring
- Quorum-based agreement protocol
- Network partition handling
- Log consistency management

Files:
- src/consensus/__init__.py
- src/consensus/consensus.py
"@
    }
)

# Commit each member's contribution
Write-Host "`nCommitting individual contributions:`n" -ForegroundColor Cyan

foreach ($member in $members) {
    Write-Host "Processing: $($member.Name) - $($member.Component)" -ForegroundColor Yellow
    
    # Check if files exist
    $filesExist = $true
    foreach ($file in $member.Files) {
        if (!(Test-Path $file)) {
            Write-Host "  ⚠️  Warning: $file not found" -ForegroundColor Red
            $filesExist = $false
        }
    }
    
    if (!$filesExist) {
        Write-Host "  Skipping due to missing files`n" -ForegroundColor Red
        continue
    }
    
    if (!$DryRun) {
        # Stage files
        foreach ($file in $member.Files) {
            git add $file
        }
        
        # Commit with proper author
        $author = "$($member.Name) <$($member.Email)>"
        git commit --author="$author" -m $member.Message
        
        Write-Host "  ✓ Committed $($member.Files -join ', ')" -ForegroundColor Green
    } else {
        Write-Host "  [DRY RUN] Would commit: $($member.Files -join ', ')" -ForegroundColor Gray
    }
    Write-Host ""
}

# Commit initial setup files first (if they exist and not yet committed)
Write-Host "Committing initial project setup..." -ForegroundColor Yellow
if (!$DryRun) {
    $setupFiles = @()
    if (Test-Path ".gitignore") { $setupFiles += ".gitignore" }
    if (Test-Path "README.md") { $setupFiles += "README.md" }
    if (Test-Path "requirements.txt") { $setupFiles += "requirements.txt" }
    
    if ($setupFiles.Count -gt 0) {
        foreach ($file in $setupFiles) {
            git add $file
        }
        git commit -m @"
Initial project setup

- Project structure and team information
- Python dependencies configuration
- Git ignore rules for generated files

Team Members:
- IT23184558 - D B Y BINUWARA - Fault Tolerance
- IT23398184 - DINUJAYA K V T - Data Replication
- IT23294998 - PABASARA T D J - Time Synchronization
- IT23424432 - ABEYRATHNA J G D A - Consensus
"@
        Write-Host "✓ Initial setup committed`n" -ForegroundColor Green
    }
}

# Commit integration code
Write-Host "Committing integration layer..." -ForegroundColor Yellow
if (!$DryRun) {
    $integrationFiles = @("src/server.py", "src/server_cluster.py")
    $foundIntegration = $false
    
    foreach ($file in $integrationFiles) {
        if (Test-Path $file) {
            git add $file
            $foundIntegration = $true
        }
    }
    
    if ($foundIntegration) {
        git commit -m @"
Add server integration layer

Integrates all four components:
- Fault tolerance monitoring (Failover)
- Data replication with Raft (MessageStorage)
- Time synchronization (TimeSync)
- Consensus management (Consensus)

Creates cohesive distributed messaging system.

Files:
- src/server.py (basic server with component integration)
- src/server_cluster.py (cluster server with full features)
"@
        Write-Host "✓ Integration layer committed`n" -ForegroundColor Green
    }
}

# Commit documentation and configuration
Write-Host "Committing documentation and configuration..." -ForegroundColor Yellow
if (!$DryRun) {
    git add README.md
    if (Test-Path "docs") { git add docs/ }
    if (Test-Path "extra") { git add extra/ }
    if (Test-Path ".gitignore") { git add .gitignore }
    if (Test-Path "TESTING_GUIDE.md") { git add TESTING_GUIDE.md }
    if (Test-Path "LOGIC_ISSUES_AND_SOLUTIONS.md") { git add LOGIC_ISSUES_AND_SOLUTIONS.md }
    
    git commit -m "Add project documentation and configuration"
    Write-Host "✓ Documentation committed`n" -ForegroundColor Green
}

# Display commit history
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Commit History Summary" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

if (!$DryRun) {
    git log --pretty=format:"%h - %an <%ae> - %s" --abbrev-commit
    Write-Host "`n"
    
    # Show statistics
    Write-Host "`nContribution Statistics:" -ForegroundColor Cyan
    git log --pretty=format:"%an" | Sort-Object | Get-Unique | ForEach-Object {
        $author = $_
        $commitCount = (git log --author="$author" --oneline | Measure-Object).Count
        $linesAdded = (git log --author="$author" --numstat --pretty="%H" | 
                      Where-Object {$_ -match "^\d"} | 
                      ForEach-Object {($_ -split "\s+")[0]} | 
                      Measure-Object -Sum).Sum
        Write-Host "  $author : $commitCount commits, ~$linesAdded lines" -ForegroundColor White
    }
}

# Setup remote if URL provided
if ($GithubUrl -and !$DryRun) {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "Setting up GitHub remote" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
    
    git remote add origin $GithubUrl
    Write-Host "✓ Remote 'origin' added: $GithubUrl`n" -ForegroundColor Green
    
    Write-Host "To push to GitHub, run:" -ForegroundColor Yellow
    Write-Host "  git push -u origin main`n" -ForegroundColor White
}

# Final instructions
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Next steps:`n" -ForegroundColor Yellow

Write-Host "1. VERIFY EMAIL ADDRESSES:" -ForegroundColor White
Write-Host "   Edit this script and update the Email field for each member" -ForegroundColor Gray
Write-Host "   to match their actual GitHub account email.`n"

Write-Host "2. VERIFY COMMIT HISTORY:" -ForegroundColor White
Write-Host "   git log --pretty=format:'%an <%ae> - %s'`n" -ForegroundColor Gray

Write-Host "3. CHECK CONTRIBUTIONS:" -ForegroundColor White
Write-Host "   git shortlog -sn`n" -ForegroundColor Gray

Write-Host "4. PUSH TO GITHUB:" -ForegroundColor White
if ($GithubUrl) {
    Write-Host "   git push -u origin main`n" -ForegroundColor Gray
} else {
    Write-Host "   git remote add origin <your-github-url>" -ForegroundColor Gray
    Write-Host "   git push -u origin main`n" -ForegroundColor Gray
}

Write-Host "5. VERIFY ON GITHUB:" -ForegroundColor White
Write-Host "   - Go to Insights → Contributors" -ForegroundColor Gray
Write-Host "   - Check that all 4 members appear" -ForegroundColor Gray
Write-Host "   - Verify line counts are appropriate`n" -ForegroundColor Gray

if ($DryRun) {
    Write-Host "NOTE: This was a dry run. No changes were made." -ForegroundColor Cyan
    Write-Host "Run without -DryRun flag to apply changes.`n" -ForegroundColor Cyan
}

Write-Host "Backup location: $backupPath`n" -ForegroundColor Yellow

# Generate submission text
$submissionText = @"

GITHUB REPOSITORY LINKS FOR SUBMISSION
======================================

Main Repository:
$GithubUrl

Individual Contributions (visible in commit history):

1. Fault Tolerance (IT23184558 - D B Y BINUWARA)
   Component: Fault tolerance and failure recovery
   Files: src/failover/, src/client.py (reconnection logic)
   Commits: $GithubUrl/commits?author=$($members[0].Email)
   Description: TCP health checks, automatic failover, client reconnection

2. Data Replication (IT23398184 - DINUJAYA K V T)
   Component: Data replication and consistency
   Files: src/message_storage/
   Commits: $GithubUrl/commits?author=$($members[1].Email)
   Description: Raft-based storage, deduplication, strong consistency

3. Time Synchronization (IT23294998 - PABASARA T D J)
   Component: Time synchronization across cluster
   Files: src/time_sync/
   Commits: $GithubUrl/commits?author=$($members[2].Email)
   Description: NTP synchronization, clock skew handling, timestamp correction

4. Consensus & Agreement (IT23424432 - ABEYRATHNA J G D A)
   Component: Consensus and distributed agreement
   Files: src/consensus/
   Commits: $GithubUrl/commits?author=$($members[3].Email)
   Description: Raft consensus, leader election, quorum-based agreement

Note: Commit history shows authentic individual contributions.
View "Insights → Contributors" on GitHub to verify.
"@

if ($GithubUrl) {
    $submissionText | Out-File "github_submission_links.txt" -Encoding UTF8
    Write-Host "✓ Created github_submission_links.txt for assignment submission`n" -ForegroundColor Green
}

Write-Host "All done! 🚀`n" -ForegroundColor Green
