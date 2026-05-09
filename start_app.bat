@echo off
echo 北海道クマ出没マップを起動しています...
echo ※このウィンドウは閉じても構いません。

:: 簡易サーバーをバックグラウンドで起動
start /min python -m http.server 8000

:: 2秒待機してからブラウザでアプリを開く
timeout /t 2 /nobreak >nul
start http://localhost:8000/web/index.html

exit
