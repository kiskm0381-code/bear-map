@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo --------------------------------------------------
echo 北海道クマ出没マップ 起動エンジン
echo --------------------------------------------------

:: プロジェクトのルートディレクトリ（このファイルがある場所）を基準にする
cd /d "%~dp0"

echo サーバーを開始しています...
:: すでにポート8000が使われている場合に備え、プロセスを一度クリーンにする（任意）
taskkill /f /im python.exe /fi "WINDOWTITLE eq BearServer*" >nul 2>&1

:: 新しいウィンドウでサーバーを起動
start "BearServer" /min python -m http.server 8000

echo 接続を待機中（3秒）...
timeout /t 3 /nobreak >nul

echo ブラウザを起動します...
start http://localhost:8000/web/index.html

echo 起動完了。このウィンドウは閉じても大丈夫です。
exit
