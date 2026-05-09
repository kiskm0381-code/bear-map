# クマ出没情報マップ 起動スクリプト
Write-Host "Starting Bear Alert Hokkaido..." -ForegroundColor Cyan

# プロジェクトのルートディレクトリに移動
$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $PSScriptRoot

# ポート8000でサーバーを起動（Pythonを使用）
Write-Host "Server starting at http://localhost:8000"
Start-Process "python" -ArgumentList "-m http.server 8000" -WindowStyle Hidden

# 少し待ってからブラウザを起動
Start-Sleep -Seconds 2
Start-Process "http://localhost:8000/web/index.html"

Write-Host "Application is running in your browser."
Write-Host "To stop the server, please close the Python window (if visible) or use Task Manager."
