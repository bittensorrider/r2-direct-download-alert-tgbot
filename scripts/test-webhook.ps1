$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Test-Path ".env")) {
    Write-Error "Create .env from .env.example first."
}

Get-Content .env | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
        [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim().Trim('"'))
    }
}

$secret = $env:WEBHOOK_SECRET
$path = if ($env:WEBHOOK_PATH) { $env:WEBHOOK_PATH } else { "/webhook/event" }
$url = "http://127.0.0.1:$($env:WEBHOOK_PORT)$path"

$body = @{
    event_type = "download"
    bucket = "my-clips"
    key = "videos/sample.mp4"
    method = "GET"
    ip = "203.0.113.10"
    country = "US"
    userAgent = "TestClient/1.0"
    referer = "https://example.com"
    range = $null
    bytesSent = 1048576
    timestamp = (Get-Date).ToUniversalTime().ToString("o")
} | ConvertTo-Json

Invoke-RestMethod -Uri $url -Method Post -Headers @{
    Authorization = "Bearer $secret"
    "Content-Type" = "application/json"
} -Body $body

Write-Host "Webhook test sent to $url"
