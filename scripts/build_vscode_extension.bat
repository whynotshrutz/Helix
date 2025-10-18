@echo off
REM Build and install Helix VS Code Extension

echo ============================================
echo Building Helix VS Code Extension
echo ============================================

cd helix-vscode

echo.
echo Step 1: Installing dependencies...
call npm install
if errorlevel 1 (
    echo ERROR: npm install failed
    exit /b 1
)

echo.
echo Step 2: Compiling TypeScript...
call npm run compile
if errorlevel 1 (
    echo ERROR: TypeScript compilation failed
    exit /b 1
)

echo.
echo Step 3: Packaging extension...
call npm run package
if errorlevel 1 (
    echo ERROR: Extension packaging failed
    exit /b 1
)

echo.
echo Step 4: Installing extension in VS Code...
code --install-extension helix-ai-1.0.0.vsix
if errorlevel 1 (
    echo ERROR: Extension installation failed
    exit /b 1
)

echo.
echo ============================================
echo SUCCESS! Extension installed.
echo ============================================
echo.
echo Next steps:
echo 1. Reload VS Code: Ctrl+R or Cmd+R
echo 2. Start AgentOS: Ctrl+Shift+P -^> "Helix: Start AgentOS Server"
echo 3. Open Chat: Ctrl+I or Cmd+I
echo 4. Type @helix- to see agents
echo.

cd ..
