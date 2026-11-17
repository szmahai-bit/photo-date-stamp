@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ================================================
echo   Push fix to GitHub (incremental, keeps history)
echo ================================================
echo.
echo This pushes the EXIF-orientation bugfix on top of
echo the existing remote main branch, keeping all commits.
echo.

echo [1/2] Show commits to push ...
git log --oneline origin/main..main

echo.
echo [2/2] Push to GitHub (browser login on first run) ...
git -c http.version=HTTP/1.1 push origin main

echo.
echo Done. View at: https://github.com/szmahai-bit/photo-date-stamp
pause
