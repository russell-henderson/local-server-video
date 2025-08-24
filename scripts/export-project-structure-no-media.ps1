<#
    Script Name: export-project-structure-no-media.ps1
    Description: Exports the directory and file structure of a given project into a text file, excluding common media files.
    Usage Example:
        .\export-project-structure-no-media.ps1 -TargetDirectory "C:\Path\To\Project" -OutputFile "project_structure.txt"
    Note: Run this script in a PowerShell terminal within VS Code.
#>

param (
    [string]$TargetDirectory = ".",
    [string]$OutputFile = "project_structure.txt"
)

# Define the excluded media file extensions.
$excludedExtensions = @(".mp4", ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp")

# Recursive function to write the project structure, excluding media files.
function Write-Tree {
    param (
        [string]$Path,
        [int]$Level = 0,
        [System.IO.StreamWriter]$Writer
    )

    # Create indentation based on the level (4 spaces per level).
    $indent = " " * ($Level * 4)

    # Get all items in the directory, sorting directories before files.
    $entries = Get-ChildItem -LiteralPath $Path | Sort-Object -Property @{Expression="PSIsContainer";Descending=$true}, Name

    foreach ($entry in $entries) {
        if ($entry.PSIsContainer) {
            # Write directory name with a trailing slash.
            $Writer.WriteLine("$indent+-- $($entry.Name)/")
            # Recursively call the function for subdirectories.
            Write-Tree -Path $entry.FullName -Level ($Level + 1) -Writer $Writer
        } else {
            # Exclude files that match any of the excluded media file extensions.
            if ($excludedExtensions -contains $entry.Extension.ToLower()) {
                continue
            }
            # Write file name.
            $Writer.WriteLine("$indent+-- $($entry.Name)")
        }
    }
}

# Create or overwrite the output file.
$writer = New-Object System.IO.StreamWriter $OutputFile, $false

# Write a header to the output file.
$writer.WriteLine("Project structure for '$TargetDirectory':")
$writer.WriteLine("Generated on: $(Get-Date)")
$writer.WriteLine("")

# Start writing the tree structure from the target directory.
Write-Tree -Path $TargetDirectory -Level 0 -Writer $writer

# Close the file writer.
$writer.Close()

Write-Host "Project structure exported to $OutputFile"
