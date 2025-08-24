<#
    Script Name: export-project-structure.ps1
    Description: Exports the directory and file structure of a given project into a text file.
    Usage Example:
        .\export-project-structure.ps1 -TargetDirectory "C:\Path\To\Project" -OutputFile "my_project_structure.txt"
    Note: Make sure to run this script in a PowerShell terminal within VS Code.
#>

param (
    [string]$TargetDirectory = ".",         # Default to the current directory if not specified.
    [string]$OutputFile = "project_structure.txt"  # Default output file name.
)

# Function to recursively write the tree structure of a directory.
function Write-Tree {
    param (
        [string]$Path,             # Current directory path.
        [int]$Level = 0,           # Current level of indentation.
        [System.IO.StreamWriter]$Writer  # Writer object to output text to a file.
    )

    # Create indentation based on the level (4 spaces per level).
    $indent = " " * ($Level * 4)

    # Get all items in the directory, sorting so that folders come before files.
    $entries = Get-ChildItem -LiteralPath $Path | Sort-Object -Property @{Expression="PSIsContainer";Descending=$true}, Name

    foreach ($entry in $entries) {
        if ($entry.PSIsContainer) {
            # Write folder name followed by a slash.
            $Writer.WriteLine("$indent+-- $($entry.Name)/")
            # Recursively call the function for subdirectories.
            Write-Tree -Path $entry.FullName -Level ($Level + 1) -Writer $Writer
        } else {
            # Write file name.
            $Writer.WriteLine("$indent+-- $($entry.Name)")
        }
    }
}

# Create or overwrite the output file.
$writer = New-Object System.IO.StreamWriter $OutputFile, $false

# Write a header to the file.
$writer.WriteLine("Project structure for '$TargetDirectory':")
$writer.WriteLine("Generated on: $(Get-Date)")
$writer.WriteLine("")

# Start writing the tree structure from the target directory.
Write-Tree -Path $TargetDirectory -Level 0 -Writer $writer

# Close the file writer.
$writer.Close()

Write-Host "Project structure exported to $OutputFile"
