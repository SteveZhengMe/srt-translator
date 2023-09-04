$envFile = "prod.env"

$envContent = Get-Content -Path $envFile

foreach ($line in $envContent) {
    if (-not ($line -match "^\s*#") -and -not [string]::IsNullOrWhiteSpace($line)) {
        $var = $line -split "=", 2
        $varName = $var[0].Trim()
        $varValue = $var[1].Trim()

        [Environment]::SetEnvironmentVariable($varName, $varValue, "Process")
    }
}

poetry run python .\app.py translate ./data/subs