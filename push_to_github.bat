@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ================================================
echo   Push photo-date-stamp to GitHub
echo ================================================
echo.
echo Remote repo szmahai-bit/photo-date-stamp is already created on GitHub.
echo This script only pushes the local code up.
echo First run will open a browser for GitHub login.
echo.

set /p GHUSER=GitHub username (Enter = szmahai-bit): 
if "%GHUSER%"=="" set GHUSER=szmahai-bit

set /p GHNAME=Author name (Enter = szmahai-bit): 
if "%GHNAME%"=="" set GHNAME=szmahai-bit

set /p GHEMAIL=Author email (Enter = noreply): 
if "%GHEMAIL%"=="" set GHEMAIL=%GHUSER%@users.noreply.github.com

echo.
echo [1/4] Init clean local repo ...
if exist .git rmdir /s /q .git
git init -b main

echo [2/4] Set author and create first commit ...
git config user.name "%GHNAME%"
git config user.email "%GHEMAIL%"
git add -A
git commit -m "Initial release: film-style date stamp GUI tool"

echo [3/4] Link remote ...
git remote add origin https://github.com/%GHUSER%/photo-date-stamp.git

echo [4/4] Push to GitHub (complete login in browser if prompted) ...
git -c http.version=HTTP/1.1 push -u origin main

echo.
echo Done. View at: https://github.com/%GHUSER%/photo-date-stamp
pause
