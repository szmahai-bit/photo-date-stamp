@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ================================================
echo   Push photo-date-stamp to GitHub (SAFE incremental)
echo ================================================
echo.
echo This script keeps local git history. It never deletes .git.
echo It rebases on the remote before pushing to avoid divergence.
echo.

set /p GHUSER=GitHub username (Enter = szmahai-bit): 
if "%GHUSER%"=="" set GHUSER=szmahai-bit

set /p GHNAME=Author name (Enter = szmahai-bit): 
if "%GHNAME%"=="" set GHNAME=szmahai-bit

set /p GHEMAIL=Author email (Enter = noreply): 
if "%GHEMAIL%"=="" set GHEMAIL=%GHUSER%@users.noreply.github.com

git config user.name "%GHNAME%"
git config user.email "%GHEMAIL%"

echo [1/5] Ensure local repo exists (history is preserved) ...
if not exist .git (
  git init -b main
  echo   Created new local repo.
) else (
  echo   Local repo exists, history kept.
)

echo [2/5] Ensure remote origin ...
git remote get-url origin >nul 2>&1
if errorlevel 1 (
  git remote add origin https://github.com/%GHUSER%/photo-date-stamp.git
  echo   Added remote origin.
) else (
  echo   Remote origin already set.
)

echo [3/5] Stage and commit local changes (if any) ...
git add -A
git diff --cached --quiet
if errorlevel 1 (
  git commit -m "Update: photo date stamp tool"
) else (
  echo   No local changes to commit.
)
git branch -M main >nul 2>&1

echo [4/5] Pull remote changes with rebase ...
git -c http.version=HTTP/1.1 pull --rebase origin main
if errorlevel 1 goto fail

echo [5/5] Push to GitHub ...
git -c http.version=HTTP/1.1 push origin main
if errorlevel 1 goto fail

echo.
echo SUCCESS. View at: https://github.com/%GHUSER%/photo-date-stamp
pause
exit /b 0

:fail
echo.
echo FAILED. Copy the error output and send it to the assistant.
pause
exit /b 1
