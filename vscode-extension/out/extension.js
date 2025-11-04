"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = require("vscode");
const chatPanel_1 = require("./chatPanel");
function getBackendUrl() {
    // Priority: VS Code settings > Environment variable > Default (Production)
    const config = vscode.workspace.getConfiguration('helix');
    const configUrl = config.get('backendUrl');
    const envUrl = process.env.HELIX_BACKEND_URL;
    const defaultUrl = 'http://3.93.17.130:8001';
    const url = configUrl || envUrl || defaultUrl;
    // Ensure no trailing slash
    return url.replace(/\/$/, '');
}
const BACKEND_URL = getBackendUrl();
// Log backend URL on activation
console.log(`🌐 Helix Backend URL: ${BACKEND_URL}`);
async function testBackendConnection(url) {
    try {
        const response = await fetch(`${url}/health`, {
            method: 'GET',
            signal: AbortSignal.timeout(5000) // 5 second timeout
        });
        const data = await response.json();
        return response.ok && data.status === 'healthy';
    }
    catch (error) {
        console.error('Backend connection test failed:', error);
        return false;
    }
}
async function* streamSSE(url, body) {
    var _a;
    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }
    const reader = (_a = response.body) === null || _a === void 0 ? void 0 : _a.getReader();
    if (!reader) {
        return;
    }
    const decoder = new TextDecoder();
    let buffer = '';
    while (true) {
        const { done, value } = await reader.read();
        if (done) {
            break;
        }
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = line.slice(6);
                if (data === '[DONE]') {
                    return;
                }
                try {
                    yield JSON.parse(data);
                }
                catch { }
            }
        }
    }
}
function activate(context) {
    console.log('🚀 Helix AI extension is now active!');
    console.log(`🌐 Backend URL: ${BACKEND_URL}`);
    const out = vscode.window.createOutputChannel('Helix AI');
    // Test backend connection on activation
    testBackendConnection(BACKEND_URL).then(isConnected => {
        if (isConnected) {
            vscode.window.showInformationMessage('✅ Helix AI: Connected to backend');
        }
        else {
            vscode.window.showWarningMessage(`⚠️ Helix AI: Cannot connect to backend at ${BACKEND_URL}. Check if backend is running.`, 'Open Settings').then(selection => {
                if (selection === 'Open Settings') {
                    vscode.commands.executeCommand('workbench.action.openSettings', 'helix.backendUrl');
                }
            });
        }
    });
    // Register chat panel provider
    const chatProvider = new chatPanel_1.HelixChatProvider(context.extensionUri, BACKEND_URL);
    context.subscriptions.push(vscode.window.registerWebviewViewProvider(chatPanel_1.HelixChatProvider.viewType, chatProvider));
    // Register clear chat command
    context.subscriptions.push(vscode.commands.registerCommand('helixMcp.clearChat', () => {
        chatProvider.clearHistory();
        vscode.window.showInformationMessage('Chat history cleared!');
    }));
    // Register open chat command
    context.subscriptions.push(vscode.commands.registerCommand('helixMcp.openChat', () => {
        vscode.commands.executeCommand('workbench.view.extension.helix-chat');
    }));
    // Register inline completion provider for automatic suggestions as you type
    const provider = vscode.languages.registerInlineCompletionItemProvider({ pattern: '**' }, // All files
    {
        async provideInlineCompletionItems(document, position, context, token) {
            // Get current line and previous lines for context
            const currentLine = document.lineAt(position.line).text;
            const precedingText = document.getText(new vscode.Range(Math.max(0, position.line - 10), 0, position.line, position.character));
            // Only trigger if user is actively typing (not just moving cursor)
            if (currentLine.trim().length === 0) {
                return { items: [] };
            }
            try {
                const res = await fetch(`${BACKEND_URL}/run`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        prompt: `Complete the following ${document.languageId} code. Return only the completion, no explanations:\n\n${precedingText}`,
                        mode: 'inline',
                        inline_completion: true // Flag to prevent file creation
                    }),
                    signal: AbortSignal.timeout(5000) // 5 second timeout
                });
                if (!res.ok) {
                    return { items: [] };
                }
                const data = await res.json();
                const suggestion = String(data.content || '').trim();
                if (suggestion && suggestion.length > 0) {
                    // Remove any markdown code blocks
                    const cleanSuggestion = suggestion
                        .replace(/```[\w]*\n/g, '')
                        .replace(/```/g, '')
                        .trim();
                    return {
                        items: [{
                                insertText: cleanSuggestion,
                                range: new vscode.Range(position, position)
                            }]
                    };
                }
            }
            catch (err) {
                // Silently fail for inline completions
                console.error('Helix inline completion error:', err);
            }
            return { items: [] };
        }
    });
    const inlineCmd = vscode.commands.registerCommand('helixMcp.inlineSuggest', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            return;
        }
        const line = editor.document.lineAt(editor.selection.active.line).text;
        try {
            const res = await fetch(`${BACKEND_URL}/run`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: `Complete this line: ${line}`, mode: 'inline' })
            });
            const data = await res.json();
            const suggestion = String(data.content || '').trim();
            if (suggestion) {
                const choice = await vscode.window.showQuickPick([suggestion], { placeHolder: 'Inline suggestion' });
                if (choice) {
                    editor.insertSnippet(new vscode.SnippetString(choice));
                }
            }
            else {
                vscode.window.showInformationMessage('No suggestion available');
            }
        }
        catch (err) {
            vscode.window.showErrorMessage('Helix backend error: ' + String(err));
        }
    });
    context.subscriptions.push(provider, inlineCmd, out);
}
function deactivate() { }
//# sourceMappingURL=extension.js.map