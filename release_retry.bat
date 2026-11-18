@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ================================================
echo   Release v1.1.0 - retry with network resilience
echo ================================================
echo.
echo The last push failed with "curl 52 Empty reply
echo from server" (a flaky GitHub connection).
echo This script retries automatically with small
echo HTTP packets and a larger buffer.
echo.

set /p GHUSER=GitHub username (Enter = szmahai-bit):
if "%GHUSER%"=="" set GHUSER=szmahai-bit

git config user.name "%GHUSER%"
git config user.email "%GHUSER%@users.noreply.github.com"

git config http.postBuffer 524288000
git config http.lowSpeedLimit 0
git config http.lowSpeedTime 600
git config http.version HTTP/1.1

echo [1/4] Stage and commit any local changes ...
git add -A
git diff --cached --quiet
if errorlevel 1 (
  git commit -m "Release v1.1.0: CI permission fix"
) else (
  echo   Nothing to commit.
)

echo [2/4] Push main (retry up to 5 times) ...
set /a TRY=0
:pushloop
set /a TRY+=1
echo   Attempt %TRY% ...
git push origin main
if not errorlevel 1 goto pushed
if %TRY% LSS 5 (
  echo   Push failed, retrying in 3 seconds ...
  timeout /t 3 /nobreak >nul
  goto pushloop
)
echo   All retries failed.
goto fail
:pushed
echo   Push succeeded.

echo [3/4] Force-update tag v1.1.0 ...
git tag -f v1.1.0
if errorlevel 1 goto fail

echo [4/4] Push tag (retry up to 5 times) ...
set /a TRY=0
:tagloop
set /a TRY+=1
echo   Attempt %TRY% ...
git push -f origin v1.1.0
if not errorlevel 1 goto tagged
if %TRY% LSS 5 (
  echo   Tag push failed, retrying in 3 seconds ...
  timeout /t 3 /nobreak >nul
  goto tagloop
)
echo   All retries failed.
goto fail
:tagged
echo   Tag pushed.

echo.
echo SUCCESS.
echo Actions: https://github.com/%GHUSER%/photo-date-stamp/actions
echo Releases: https://github.com/%GHUSER%/photo-date-stamp/releases/tag/v1.1.0
echo Wait a few minutes for the macOS build to finish.
pause
exit /b 0

:fail
echo.
echo FAILED. Copy the error output and send it to the assistant.
pause
exit /b 1
