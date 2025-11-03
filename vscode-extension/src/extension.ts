import * as vscode from 'vscode';
import { HelixChatProvider } from './chatPanel';

function getBackendUrl(): string {
    // Priority: VS Code settings > Environment variable > Default
    const config = vscode.workspace.getConfiguration('helix');
    const configUrl = config.get<string>('backendUrl');
    const envUrl = process.env.HELIX_BACKEND_URL;
    return configUrl || envUrl || 'http://127.0.0.1:8001';
}

const BACKEND_URL = getBackendUrl();

async function* streamSSE(url: string, body: any): AsyncGenerator<any> {
    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) { return; }

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
        const { done, value } = await reader.read();
        if (done) { break; }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = line.slice(6);
                if (data === '[DONE]') { return; }
                try {
                    yield JSON.parse(data);
                } catch { }
            }
        }
    }
}

export function activate(context: vscode.ExtensionContext) {
    console.log('🚀 Helix AI extension is now active!');
    const out = vscode.window.createOutputChannel('Helix AI');

    // Register chat panel provider
    const chatProvider = new HelixChatProvider(context.extensionUri, BACKEND_URL);
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(
            HelixChatProvider.viewType,
            chatProvider
        )
    );

    // Register clear chat command
    context.subscriptions.push(
        vscode.commands.registerCommand('helixMcp.clearChat', () => {
            chatProvider.clearHistory();
            vscode.window.showInformationMessage('Chat history cleared!');
        })
    );

    // Register open chat command
    context.subscriptions.push(
        vscode.commands.registerCommand('helixMcp.openChat', () => {
            vscode.commands.executeCommand('workbench.view.extension.helix-chat');
        })
    );

    // Register inline completion provider for automatic suggestions as you type
    const provider = vscode.languages.registerInlineCompletionItemProvider(
        { pattern: '**' }, // All files
        {
            async provideInlineCompletionItems(document, position, context, token) {
                // Get current line and previous lines for context
                const currentLine = document.lineAt(position.line).text;
                const precedingText = document.getText(new vscode.Range(
                    Math.max(0, position.line - 10),
                    0,
                    position.line,
                    position.character
                ));

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
                            inline_completion: true  // Flag to prevent file creation
                        }),
                        signal: AbortSignal.timeout(5000) // 5 second timeout
                    });

                    if (!res.ok) {
                        return { items: [] };
                    }

                    const data = await res.json() as { content?: string };
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
                } catch (err) {
                    // Silently fail for inline completions
                    console.error('Helix inline completion error:', err);
                }

                return { items: [] };
            }
        }
    );

    const inlineCmd = vscode.commands.registerCommand('helixMcp.inlineSuggest', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) { return; }
        const line = editor.document.lineAt(editor.selection.active.line).text;
        try {
            const res = await fetch(`${BACKEND_URL}/run`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: `Complete this line: ${line}`, mode: 'inline' })
            });
            const data = await res.json() as { content?: string };
            const suggestion = String(data.content || '').trim();
            if (suggestion) {
                const choice = await vscode.window.showQuickPick([suggestion], { placeHolder: 'Inline suggestion' });
                if (choice) {
                    editor.insertSnippet(new vscode.SnippetString(choice));
                }
            } else {
                vscode.window.showInformationMessage('No suggestion available');
            }
        } catch (err) {
            vscode.window.showErrorMessage('Helix backend error: ' + String(err));
        }
    });

    context.subscriptions.push(provider, inlineCmd, out);
}

export function deactivate() {}
