@echo off
REM Quick build and package script for Helix VS Code Extension

echo Building Helix VS Code Extension...
echo.

cd vscode-extension

REM Install dependencies
echo Installing dependencies...
call npm install

REM Build TypeScript
echo Building TypeScript...
call npm run build

REM Install vsce if not present
where vsce >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing vsce...
    call npm install -g vsce
)

REM Package extension
echo Packaging extension...
call vsce package

echo.
echo Extension packaged successfully!
echo.
dir /B *.vsix
echo.
echo To install:
echo    code --install-extension helix-mcp-client-*.vsix
echo.
echo To distribute:
echo    Share the .vsix file with users
echo.
echo To publish to marketplace:
echo    vsce publish
