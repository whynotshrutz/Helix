"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = require("vscode");
const BACKEND_URL = process.env.HELIX_BACKEND_URL || 'http://127.0.0.1:8000';
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
    console.log('🚀 Helix MCP extension is now active!');
    const out = vscode.window.createOutputChannel('Helix MCP');
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
    const chatCmd = vscode.commands.registerCommand('helixMcp.chat', async () => {
        // Check if workspace folder is open
        if (!vscode.workspace.workspaceFolders || vscode.workspace.workspaceFolders.length === 0) {
            const action = await vscode.window.showWarningMessage('No folder is open. Helix needs a workspace folder to create files.', 'Open Folder');
            if (action === 'Open Folder') {
                await vscode.commands.executeCommand('vscode.openFolder');
            }
            return;
        }
        const prompt = await vscode.window.showInputBox({ prompt: 'Ask Helix' });
        if (!prompt) {
            return;
        }
        // Show progress notification instead of output channel
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Helix is working...",
            cancellable: false
        }, async (progress) => {
            try {
                let fullResponse = '';
                // Use streaming to get response
                for await (const event of streamSSE(`${BACKEND_URL}/run`, { prompt, mode: 'chat', stream: true })) {
                    if (event.error) {
                        vscode.window.showErrorMessage('Helix: ' + event.error);
                        return;
                    }
                    if (event.content) {
                        fullResponse += event.content;
                    }
                }
                // Debug: Log the response
                console.log('Full AI response:', fullResponse);
                // Parse for CREATE_FILE markers - try multiple patterns
                // Pattern 1: CREATE_FILE: filename followed by code block
                const filePattern1 = /CREATE_FILE:\s*([^\n]+)\s*```[\w]*\s*\n([\s\S]*?)```/gi;
                // Pattern 2: Just detect if AI is trying to create code
                const filePattern2 = /```(\w+)\s*\n([\s\S]*?)```/gi;
                let match;
                let filesCreated = 0;
                // Try pattern 1 first (explicit CREATE_FILE marker)
                while ((match = filePattern1.exec(fullResponse)) !== null) {
                    const filename = match[1].trim();
                    const code = match[2].trim();
                    console.log(`Found file to create: ${filename}`);
                    // Get workspace folder
                    const workspaceFolders = vscode.workspace.workspaceFolders;
                    if (!workspaceFolders) {
                        vscode.window.showErrorMessage('No workspace folder open');
                        return;
                    }
                    // Create file URI
                    const fileUri = vscode.Uri.joinPath(workspaceFolders[0].uri, filename);
                    try {
                        // Write file
                        await vscode.workspace.fs.writeFile(fileUri, Buffer.from(code, 'utf-8'));
                        // Open the file in editor
                        const doc = await vscode.workspace.openTextDocument(fileUri);
                        await vscode.window.showTextDocument(doc, { preview: false });
                        filesCreated++;
                        console.log(`Successfully created: ${filename}`);
                    }
                    catch (err) {
                        console.error(`Failed to create ${filename}:`, err);
                        vscode.window.showErrorMessage(`Failed to create ${filename}: ${err}`);
                    }
                }
                if (filesCreated > 0) {
                    vscode.window.showInformationMessage(`✅ Created ${filesCreated} file(s)`);
                }
                else {
                    // If no files created, show response in output
                    console.log('No CREATE_FILE markers found, showing in output channel');
                    out.appendLine(`\n> ${prompt}\n`);
                    out.appendLine(fullResponse);
                    out.show(true);
                }
            }
            catch (err) {
                vscode.window.showErrorMessage('Helix backend error: ' + String(err));
            }
        });
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
    context.subscriptions.push(provider, chatCmd, inlineCmd, out);
}
function deactivate() { }
//# sourceMappingURL=extension.js.map