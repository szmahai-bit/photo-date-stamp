@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ================================================
echo   Release v1.1.0 - Intel Mac build (retry)
echo ================================================
echo.
echo Re-pushes the CI permission fix, then force-updates
echo tag v1.1.0 to trigger a clean rebuild. This time
echo GitHub Actions can attach the .dmg + .exe to Releases.
echo (Previous run built fine; only the Release upload
echo  failed due to missing token permission - now fixed.)
echo.

set /p GHUSER=GitHub username (Enter = szmahai-bit):
if "%GHUSER%"=="" set GHUSER=szmahai-bit

git config user.name "%GHUSER%"
git config user.email "%GHUSER%@users.noreply.github.com"

echo [1/5] Stage and commit any local changes ...
git add -A
git diff --cached --quiet
if errorlevel 1 (
  git commit -m "Release v1.1.0: Intel macOS build"
) else (
  echo   Nothing to commit.
)

echo [2/5] Pull remote with rebase ...
git -c http.version=HTTP/1.1 pull --rebase origin main
if errorlevel 1 goto fail

echo [3/5] Push main ...
git -c http.version=HTTP/1.1 push origin main
if errorlevel 1 goto fail

echo [4/5] Create local tag v1.1.0 ...
git tag -f v1.1.0
if errorlevel 1 goto fail

echo [5/5] Push tag (triggers CI build + Release) ...
git -c http.version=HTTP/1.1 push -f origin v1.1.0
if errorlevel 1 goto fail

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
