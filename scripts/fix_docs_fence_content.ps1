$root = 'z:\local-video-server\docs'
$files = Get-ChildItem -Path $root -Filter *.md
foreach ($f in $files) {
    $path = $f.FullName
    $text = Get-Content -Raw -LiteralPath $path -Encoding UTF8 -ErrorAction Stop
    $lines = $text -split "\r?\n"
    $changed = $false
    $i = 0
    while ($i -lt $lines.Length) {
        if ($lines[$i] -match '^```\s*$') {
            $start = $i
            $j = $i + 1
            while ($j -lt $lines.Length -and -not ($lines[$j] -match '^```\s*$')) { $j++ }
            if ($j -ge $lines.Length) { break }
            $content = $lines[$start+1..($j-1)]
            # decide: if content is purely numbered/bulleted list, remove fences
            $allList = $true
            foreach ($ln in $content) {
                if ($ln -match '^\s*$') { continue }
                if ($ln -match '^\s*([0-9]+\.|\-|\*|\+)\s+') { continue }
                $allList = $false; break
            }
            if ($allList) {
                # remove the fence lines
                $lines = $lines[0..($start-1)] + $content + $lines[($j+1)..($lines.Length-1)]
                $changed = $true
                $i = $start + $content.Length
                continue
            } else {
                # add language if missing
                $firstNonEmpty = $content | Where-Object { $_ -notmatch '^\s*$' } | Select-Object -First 1
                $lang = 'bash'
                if ($firstNonEmpty -match '^(from |def |class |import |# type:|@pytest)') { $lang = 'python' }
                elseif ($firstNonEmpty -match '^\$|^sudo |^\.|^python |^pip |^gem |^choco |^npm |^curl |^wget ') { $lang = 'bash' }
                elseif ($firstNonEmpty -match '^(<script|function |console\.log|document\.|window\.)') { $lang = 'javascript' }
                elseif ($firstNonEmpty -match '^[.#]?[A-Za-z0-9_-]+\s*\{|^[a-z-]+:\s') { $lang = 'css' }
                elseif ($firstNonEmpty -match '^(Set-|Get-|New-|Remove-|Import-Module|\.\\|PS )') { $lang = 'powershell' }
                $lines[$start] = "```$lang"
                $changed = $true
                $i = $j + 1
                continue
            }
        }
        $i++
    }
    if ($changed) {
        $text = $lines -join "`r`n"
        Set-Content -LiteralPath $path -Value $text -Encoding UTF8
        Write-Output "Fixed fences: $path"
    }
}
Write-Output 'Done'
