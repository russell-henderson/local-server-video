$root = 'z:\local-video-server\docs'
$files = Get-ChildItem -Path $root -Filter *.md
foreach ($f in $files) {
    $path = $f.FullName
    $text = Get-Content -Raw -LiteralPath $path -Encoding UTF8 -ErrorAction Stop
    $lines = $text -split "\r?\n"
    if ($lines.Length -lt 2) { continue }
    $firstLine = $lines[0]
    # find first non-empty line index
    $secondIndex = 1
    while ($secondIndex -lt $lines.Length -and $lines[$secondIndex] -match '^\s*$') { $secondIndex++ }
    if ($firstLine -match '^\s*`{3,}.*' -and $secondIndex -lt $lines.Length -and $lines[$secondIndex] -match '^#') {
        # remove first line
        $lines = $lines[1..($lines.Length-1)]
        # remove trailing closing fence if present
        # find last non-empty line index
        $k = $lines.Length - 1
        while ($k -ge 0 -and $lines[$k] -match '^\s*$') { $k-- }
        if ($k -ge 0 -and $lines[$k] -match '^\s*`{3,}.*') {
            $lines = $lines[0..($k-1)]
        }
        $text = $lines -join "`r`n"
        Set-Content -LiteralPath $path -Value $text -Encoding UTF8
        Write-Output "Stripped outer fence: $path"
    }
}
Write-Output 'Done'
