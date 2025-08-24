<#
    Script Name: export-code-descriptions-openai.ps1
    Description: 
        Scans a project directory for code files (excluding media files) and utilizes the OpenAI API 
        (using GPT-4) to generate a detailed, analytical description for each file. The descriptions 
        are saved in an output text file.
    Requirements:
        - PowerShell (preferably using the VS Code integrated terminal).
        - An OpenAI API key set in the environment variable $env:OPENAI_API_KEY.
    Usage Example:
        .\export-code-descriptions-openai.ps1 -TargetDirectory "C:\Path\To\Project" -OutputFile "code_descriptions.txt"
#>

param (
    [string]$TargetDirectory = ".",
    [string]$OutputFile = "code_descriptions.txt"
)

# Ensure that the OpenAI API key is set in the environment variable.
if (-not $env:OPENAI_API_KEY) {
    Write-Error "The OpenAI API key is not set. Please set the environment variable 'OPENAI_API_KEY' before running the script."
    exit
}

# Define the excluded media file extensions.
$excludedExtensions = @(
    ".mp4", ".avi", ".mov", ".mkv", 
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp",
    ".mp3", ".wav", ".flac"
)

# Function to call the OpenAI API (using GPT-4) and retrieve an analytical description for a code file.
function Get-OpenAIDescription {
    param (
        [string]$fileName,
        [string]$fileExtension,
        [string]$fileSnippet = ""
    )

    # Build the prompt for GPT-4.
    $prompt = "You are a code analyst. Analyze the file named '$fileName' with extension '$fileExtension'. " +
              "Provide a detailed, analytical description of its purpose, functionality, and role within the project. " +
              "Include details on the technologies, libraries, and design patterns used, and explain how it contributes " +
              "to the overall system architecture."
    if ($fileSnippet -ne "") {
        $prompt += " Here is a snippet for additional context: $fileSnippet"
    }

    # Define the request body for the API.
    $body = @{
        model = "gpt-4"
        messages = @(
            @{ role = "system"; content = "You are a highly analytical code assistant." }
            @{ role = "user"; content = $prompt }
        )
        max_tokens = 150
        temperature = 0.5
    } | ConvertTo-Json

    # Prepare headers for the API call.
    $headers = @{
        "Content-Type"  = "application/json"
        "Authorization" = "Bearer $($env:OPENAI_API_KEY)"
    }

    # Call the OpenAI API endpoint.
    try {
        $response = Invoke-RestMethod -Uri "https://api.openai.com/v1/chat/completions" -Method Post -Headers $headers -Body $body
        return $response.choices[0].message.content.Trim()
    }
    catch {
        Write-Warning "API call failed for file '$fileName'. Error: $_"
        return "Error retrieving description."
    }
}

# Resolve the absolute path for the target directory.
$targetFullPath = (Resolve-Path $TargetDirectory).Path

# Get all code files in the target directory, excluding media files.
$files = Get-ChildItem -Path $TargetDirectory -Recurse -File | Where-Object {
    -not ($excludedExtensions -contains $_.Extension.ToLower())
}

# Create or overwrite the output file.
$writer = New-Object System.IO.StreamWriter $OutputFile, $false

# Write header information to the output file.
$writer.WriteLine("Project code descriptions for '$TargetDirectory':")
$writer.WriteLine("Generated on: $(Get-Date)")
$writer.WriteLine("")

# Process each file and get an analytical description using the OpenAI API.
foreach ($file in $files) {
    # Calculate the file's relative path.
    $relativePath = $file.FullName.Substring($targetFullPath.Length).TrimStart("\", "/")

    # Retrieve a snippet of the file's content for context (first 10 lines).
    $snippet = ""
    try {
        $snippet = (Get-Content -Path $file.FullName -TotalCount 10 -ErrorAction Stop) -join " "
        if ($snippet.Length -gt 500) {
            $snippet = $snippet.Substring(0,500)
        }
    }
    catch {
        $snippet = ""
    }
    
    # Get the analytical description from the OpenAI API.
    $description = Get-OpenAIDescription -fileName $file.Name -fileExtension $file.Extension -fileSnippet $snippet

    # Write the file's relative path and its analytical description to the output file.
    $writer.WriteLine("File: $relativePath")
    $writer.WriteLine("Description: $description")
    $writer.WriteLine("")
}

# Close the writer.
$writer.Close()

Write-Host "Analytical code descriptions exported to $OutputFile"
