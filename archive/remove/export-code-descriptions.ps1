<#
    Script Name: export-code-descriptions.ps1
    Description: Scans a project directory (excluding media files) and exports a text file that lists each code file along with a general description based on its file type.
    Usage Example:
        .\export-code-descriptions.ps1 -TargetDirectory "C:\Path\To\Project" -OutputFile "code_descriptions.txt"
    Note: Run this script in a PowerShell terminal within VS Code.
#>

param (
    [string]$TargetDirectory = ".",
    [string]$OutputFile = "code_descriptions.txt"
)

# Define the excluded media file extensions.
$excludedExtensions = @(
    ".mp4", ".avi", ".mov", ".mkv", 
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp",
    ".mp3", ".wav", ".flac"
)

# Mapping of file extensions to general descriptions.
$descriptions = @{
    ".py"   = "Python file – likely contains main application logic or utility functions."
    ".html" = "HTML file – used for webpage templates and UI layout."
    ".css"  = "CSS file – provides styling and layout for webpages."
    ".json" = "JSON file – stores configuration, data, or settings in a structured format."
    ".ps1"  = "PowerShell script – automates tasks or performs project operations."
    ".js"   = "JavaScript file – contains client-side or server-side logic."
    # Add more mappings as needed.
}

# Create or overwrite the output file.
$writer = New-Object System.IO.StreamWriter $OutputFile, $false

# Write header to the output file.
$writer.WriteLine("Project code descriptions for '$TargetDirectory':")
$writer.WriteLine("Generated on: $(Get-Date)")
$writer.WriteLine("")

# Resolve the absolute path for the target directory.
$targetFullPath = (Resolve-Path $TargetDirectory).Path

# Recursively get all files in the target directory, excluding media files.
$files = Get-ChildItem -Path $TargetDirectory -Recurse -File | Where-Object {
    -not ($excludedExtensions -contains $_.Extension.ToLower())
}

foreach ($file in $files) {
    # Determine description based on the file extension.
    $ext = $file.Extension.ToLower()
    $desc = $descriptions[$ext]
    if (-not $desc) {
        $desc = "General code file – no specific description available."
    }

    # Calculate the file's relative path.
    $relativePath = $file.FullName.Substring($targetFullPath.Length).TrimStart("\","/")

    # Write file details to the output file.
    $writer.WriteLine("File: $relativePath")
    $writer.WriteLine("Description: $desc")
    $writer.WriteLine("")
}

# Close the output file.
$writer.Close()

Write-Host "Code descriptions exported to $OutputFile"
