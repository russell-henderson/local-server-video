$root = 'z:\local-video-server\docs'
$files = Get-ChildItem -Path $root -Recurse -Filter *.md
foreach ($f in $files) {
    $path = $f.FullName
    $text = Get-Content -Raw -LiteralPath $path
    $orig = $text
    # remove leading fence lines (```...)
    while ($text -match '^[ \t]*`{3,}.*\r?\n') {
        $text = $text -replace '^[ \t]*`{3,}.*\r?\n',''
    }
    # remove trailing fence lines
    while ($text -match '\r?\n[ \t]*`{3,}.*\s*\z') {
        $text = $text -replace '\r?\n[ \t]*`{3,}.*\s*\z',''
    }
    # ensure blank line after first H1 heading (use Regex.Replace with multiline)
    $text = [regex]::Replace($text, '^(# .+?)\r?\n(?!\r?\n)', '$1' + "`r`n`r`n", [System.Text.RegularExpressions.RegexOptions]::Multiline)
    # replace tabs with two spaces
    $text = $text -replace "`t", '  '
    # Add language to fence blocks in top-level docs (docs/*.md) only
    if ($path -like "*\\docs\\*.md") {
        $lines = $text -split "\r?\n"
        for ($i = 0; $i -lt $lines.Length; $i++) {
            if ($lines[$i] -match '^```\s*$') {
                # find next non-empty line
                $j = $i + 1
                while ($j -lt $lines.Length -and $lines[$j] -match '^\s*$') { $j++ }
                $lang = $null
                if ($j -lt $lines.Length) {
                    $next = $lines[$j].Trim()
                    if ($next -match '^(from |def |class |import |# type:|@pytest)') { $lang = 'python' }
                    elseif ($next -match '^\$|^sudo |^\.|^python |^pip |^gem |^choco |^npm |^curl |^wget ') { $lang = 'bash' }
                    elseif ($next -match '^(<script|function |console\.log|document\.|window\.)') { $lang = 'javascript' }
                    elseif ($next -match '^[.#]?[A-Za-z0-9_-]+\s*\{|^[a-z-]+:\s') { $lang = 'css' }
                    elseif ($next -match '^(Set-|Get-|New-|Remove-|Import-Module|\.\\|PS )') { $lang = 'powershell' }
                    else { $lang = 'bash' }
                } else { $lang = 'bash' }
                $lines[$i] = "```$lang"
            }
        }
        $text = $lines -join "`r`n"
    }
    # Additional aggressive cleanup for stubborn files: if leading lines contain only backticks
    $lines = $text -split "\r?\n"
    $firstHeading = $lines | Select-String -Pattern '^(# )' -SimpleMatch | Select-Object -First 1
    if ($firstHeading) {
        $startIndex = ($lines | Select-String -Pattern '^(# )' -SimpleMatch | Select-Object -First 1).LineNumber - 1
        $lines = $lines[$startIndex..($lines.Length - 1)]
        # trim leading/trailing backtick-only lines
        while ($lines.Count -gt 0 -and ($lines[0] -match '^\s*`{3,}\s*$' -or $lines[0] -match '^\s*$')) { $lines = $lines[1..($lines.Count-1)] }
        while ($lines.Count -gt 0 -and ($lines[-1] -match '^\s*`{3,}\s*$' -or $lines[-1] -match '^\s*$')) { $lines = $lines[0..($lines.Count-2)] }
        $text = ($lines -join "`r`n")
    }
    if ($text -ne $orig) {
        Set-Content -LiteralPath $path -Value $text
        Write-Output "Fixed: $path"
    } else {
        Write-Output "NoChange: $path"
    }
}
Write-Output 'Done'
