import * as vscode from 'vscode';

export class HelixChatProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'helixChatView';
    private _view?: vscode.WebviewView;
    private _backendUrl: string;
    private _chatHistory: Array<{ role: 'user' | 'assistant'; content: string }> = [];
    private _attachedFiles: Array<{ path: string; name: string; content: string }> = [];

    constructor(
        private readonly _extensionUri: vscode.Uri,
        backendUrl: string
    ) {
        this._backendUrl = backendUrl;
    }

    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken
    ) {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri]
        };

        webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);

        // Handle messages from the webview
        webviewView.webview.onDidReceiveMessage(async data => {
            switch (data.type) {
                case 'sendMessage':
                    await this._handleUserMessage(data.message);
                    break;
                case 'clearHistory':
                    this._chatHistory = [];
                    this._attachedFiles = [];
                    this._sendMessage({ type: 'clearMessages' });
                    break;
                case 'attachFiles':
                    await this._handleFileAttachment();
                    break;
                case 'removeAttachment':
                    this._attachedFiles = this._attachedFiles.filter(f => f.path !== data.path);
                    this._sendMessage({ type: 'updateAttachments', files: this._attachedFiles.map(f => ({ name: f.name, path: f.path })) });
                    break;
                case 'filesDropped':
                    await this._handleDroppedFiles(data.files);
                    break;
            }
        });
    }

    private async _handleFileAttachment() {
        const options: vscode.OpenDialogOptions = {
            canSelectMany: true,
            canSelectFiles: true,
            canSelectFolders: true,
            openLabel: 'Attach Files/Folders'
        };

        const fileUris = await vscode.window.showOpenDialog(options);
        if (fileUris && fileUris.length > 0) {
            await this._processFileUris(fileUris);
        }
    }

    private async _handleDroppedFiles(filePaths: string[]) {
        const fileUris = filePaths.map(path => vscode.Uri.file(path));
        await this._processFileUris(fileUris);
    }

    private async _processFileUris(fileUris: vscode.Uri[]) {
        for (const fileUri of fileUris) {
            const stat = await vscode.workspace.fs.stat(fileUri);
            
            if (stat.type === vscode.FileType.Directory) {
                // Process directory
                await this._processDirectory(fileUri);
            } else {
                // Process file
                await this._processFile(fileUri);
            }
        }
        
        this._sendMessage({ 
            type: 'updateAttachments', 
            files: this._attachedFiles.map(f => ({ name: f.name, path: f.path })) 
        });
    }

    private async _processDirectory(dirUri: vscode.Uri) {
        const entries = await vscode.workspace.fs.readDirectory(dirUri);
        
        for (const [name, type] of entries) {
            // Skip hidden files and node_modules
            if (name.startsWith('.') || name === 'node_modules' || name === '__pycache__') {
                continue;
            }

            const childUri = vscode.Uri.joinPath(dirUri, name);
            
            if (type === vscode.FileType.Directory) {
                await this._processDirectory(childUri);
            } else if (type === vscode.FileType.File) {
                await this._processFile(childUri);
            }
        }
    }

    private async _processFile(fileUri: vscode.Uri) {
        try {
            const content = await vscode.workspace.fs.readFile(fileUri);
            const textContent = Buffer.from(content).toString('utf8');
            
            // Only attach text files (skip binary)
            if (this._isTextFile(fileUri.fsPath)) {
                this._attachedFiles.push({
                    path: fileUri.fsPath,
                    name: fileUri.fsPath.split(/[\\/]/).pop() || fileUri.fsPath,
                    content: textContent
                });
            }
        } catch (error) {
            console.error('Error reading file:', error);
        }
    }

    private _isTextFile(filePath: string): boolean {
        const textExtensions = [
            '.txt', '.md', '.js', '.ts', '.jsx', '.tsx', '.py', '.java', '.c', '.cpp', '.h', '.hpp',
            '.cs', '.go', '.rs', '.rb', '.php', '.html', '.css', '.scss', '.json', '.xml', '.yaml', '.yml',
            '.sh', '.bat', '.ps1', '.sql', '.r', '.m', '.swift', '.kt', '.dart', '.vue', '.svelte'
        ];
        
        return textExtensions.some(ext => filePath.toLowerCase().endsWith(ext));
    }

    private async _handleUserMessage(userMessage: string) {
        if (!userMessage.trim()) return;

        // Build enhanced message with file context and web URLs
        let enhancedMessage = userMessage;
        
        // Add file context if files are attached
        if (this._attachedFiles.length > 0) {
            enhancedMessage = `User has attached ${this._attachedFiles.length} file(s) for context:\n\n`;
            
            for (const file of this._attachedFiles) {
                enhancedMessage += `File: ${file.name}\n`;
                enhancedMessage += `Path: ${file.path}\n`;
                enhancedMessage += `Content:\n\`\`\`\n${file.content}\n\`\`\`\n\n`;
            }
            
            enhancedMessage += `User's request: ${userMessage}`;
        }
        
        // Detect and highlight web URLs for reference
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        const urls = userMessage.match(urlRegex);
        if (urls && urls.length > 0) {
            enhancedMessage += `\n\n🔗 Web references detected: ${urls.join(', ')}`;
            enhancedMessage += `\n\nPlease fetch and refer to the content from these URLs for the user's requirement.`;
        }

        // Add user message to history
        this._chatHistory.push({ role: 'user', content: enhancedMessage });
        
        // Show user message in UI (original message with attachments)
        this._sendMessage({
            type: 'addMessage',
            role: 'user',
            content: userMessage,
            attachments: this._attachedFiles.map(f => ({ name: f.name, path: f.path }))
        });

        // Show loading state
        this._sendMessage({ type: 'setLoading', loading: true });

        try {
            // Get workspace folder for file operations
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            
            // Send request to backend with enhanced message
            const response = await fetch(`${this._backendUrl}/run`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt: enhancedMessage,  // Send enhanced message with file context
                    mode: 'chat',
                    stream: false
                })
            });
            
            // Clear attachments after sending
            const hadAttachments = this._attachedFiles.length > 0;
            this._attachedFiles = [];
            if (hadAttachments) {
                this._sendMessage({ type: 'updateAttachments', files: [] });
            }

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json() as {
                content?: string;
                mode?: string;
                agent?: string;
            };

            const assistantMessage = data.content || 'No response received.';
            
            // Add assistant message to history
            this._chatHistory.push({ role: 'assistant', content: assistantMessage });

            // Parse for file creation markers
            const filePattern = /CREATE_FILE:\s*([^\n]+)\s*```[\w]*\s*\n([\s\S]*?)```/gi;
            let match;
            let filesCreated: string[] = [];

            while ((match = filePattern.exec(assistantMessage)) !== null) {
                const filename = match[1].trim();
                const code = match[2].trim();

                if (workspaceFolder) {
                    const filePath = vscode.Uri.joinPath(workspaceFolder.uri, filename);
                    await vscode.workspace.fs.writeFile(filePath, Buffer.from(code, 'utf8'));
                    filesCreated.push(filename);
                    
                    // Open the created file
                    const doc = await vscode.workspace.openTextDocument(filePath);
                    await vscode.window.showTextDocument(doc, { preview: false });
                }
            }

            // Show assistant message in UI
            this._sendMessage({
                type: 'addMessage',
                role: 'assistant',
                content: assistantMessage,
                agent: data.agent,
                filesCreated: filesCreated
            });

        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
            
            this._sendMessage({
                type: 'addMessage',
                role: 'assistant',
                content: `❌ Error: ${errorMessage}`
            });
        } finally {
            this._sendMessage({ type: 'setLoading', loading: false });
        }
    }

    private _sendMessage(message: any) {
        if (this._view) {
            this._view.webview.postMessage(message);
        }
    }

    public clearHistory() {
        this._chatHistory = [];
        this._sendMessage({ type: 'clearMessages' });
    }

    private _getHtmlForWebview(webview: vscode.Webview) {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Helix AI Chat</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: var(--vscode-font-family);
            font-size: var(--vscode-font-size);
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
            height: 100vh;
            display: flex;
            flex-direction: column;
        }

        #chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .message {
            display: flex;
            flex-direction: column;
            gap: 4px;
            padding: 12px;
            border-radius: 8px;
            max-width: 90%;
            word-wrap: break-word;
        }

        .message.user {
            align-self: flex-end;
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
        }

        .message.assistant {
            align-self: flex-start;
            background-color: var(--vscode-input-background);
            border: 1px solid var(--vscode-input-border);
        }

        .message-header {
            font-size: 11px;
            opacity: 0.7;
            font-weight: 600;
            margin-bottom: 4px;
        }

        .message-content {
            line-height: 1.5;
            white-space: pre-wrap;
        }

        .message-content code {
            background-color: var(--vscode-textCodeBlock-background);
            padding: 2px 4px;
            border-radius: 3px;
            font-family: var(--vscode-editor-font-family);
        }

        .message-content pre {
            background-color: var(--vscode-textCodeBlock-background);
            padding: 8px;
            border-radius: 4px;
            overflow-x: auto;
            margin: 8px 0;
        }

        .files-created {
            margin-top: 8px;
            padding: 8px;
            background-color: var(--vscode-textCodeBlock-background);
            border-radius: 4px;
            font-size: 12px;
        }

        .files-created-title {
            font-weight: 600;
            margin-bottom: 4px;
            color: var(--vscode-symbolIcon-fileForeground);
        }

        #input-container {
            padding: 12px;
            background-color: var(--vscode-input-background);
            border-top: 1px solid var(--vscode-input-border);
            display: flex;
            gap: 8px;
        }

        #message-input {
            flex: 1;
            padding: 8px 12px;
            background-color: var(--vscode-input-background);
            color: var(--vscode-input-foreground);
            border: 1px solid var(--vscode-input-border);
            border-radius: 4px;
            outline: none;
            font-family: var(--vscode-font-family);
            font-size: var(--vscode-font-size);
            resize: none;
            min-height: 36px;
            max-height: 120px;
        }

        #message-input:focus {
            border-color: var(--vscode-focusBorder);
        }

        #send-button {
            padding: 8px 16px;
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 600;
            transition: background-color 0.2s;
        }

        #send-button:hover:not(:disabled) {
            background-color: var(--vscode-button-hoverBackground);
        }

        #send-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .loading {
            display: none;
            padding: 12px;
            text-align: center;
            color: var(--vscode-descriptionForeground);
            font-style: italic;
        }

        .loading.active {
            display: block;
        }

        .empty-state {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 32px;
            text-align: center;
            color: var(--vscode-descriptionForeground);
        }

        .empty-state-icon {
            font-size: 48px;
            margin-bottom: 16px;
            opacity: 0.5;
        }

        .empty-state-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 8px;
        }

        .empty-state-subtitle {
            font-size: 13px;
            opacity: 0.7;
        }

        /* Drag and drop styles */
        #chat-container.drag-over {
            border: 2px dashed var(--vscode-focusBorder);
            background-color: var(--vscode-editor-inactiveSelectionBackground);
        }

        .drag-overlay {
            display: none;
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 100px;
            background-color: rgba(0, 0, 0, 0.5);
            z-index: 1000;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 24px;
            font-weight: 600;
        }

        .drag-overlay.visible {
            display: flex;
        }

        /* Attachments display */
        #attachments-container {
            display: none;
            padding: 8px 12px;
            background-color: var(--vscode-editor-background);
            border-top: 1px solid var(--vscode-input-border);
            flex-wrap: wrap;
            gap: 6px;
            max-height: 120px;
            overflow-y: auto;
        }

        #attachments-container.visible {
            display: flex;
        }

        .attachment-chip {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 8px;
            background-color: var(--vscode-badge-background);
            color: var(--vscode-badge-foreground);
            border-radius: 12px;
            font-size: 12px;
            max-width: 200px;
        }

        .attachment-name {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .attachment-remove {
            cursor: pointer;
            padding: 0 4px;
            font-weight: bold;
            opacity: 0.7;
        }

        .attachment-remove:hover {
            opacity: 1;
        }

        #attach-button {
            padding: 8px;
            background-color: var(--vscode-button-secondaryBackground);
            color: var(--vscode-button-secondaryForeground);
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            line-height: 1;
            transition: background-color 0.2s;
        }

        #attach-button:hover {
            background-color: var(--vscode-button-secondaryHoverBackground);
        }

        .message.user .attachment-info {
            margin-top: 6px;
            padding: 6px;
            background-color: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
            font-size: 11px;
            opacity: 0.8;
        }
    </style>
</head>
<body>
    <div class="drag-overlay" id="drag-overlay">
        📁 Drop files or folders here
    </div>
    <div id="chat-container">
        <div class="empty-state">
            <div class="empty-state-icon">💬</div>
            <div class="empty-state-title">Welcome to Helix AI</div>
            <div class="empty-state-subtitle">Ask me anything about your code!<br>Drag & drop files/folders to attach them.</div>
        </div>
    </div>
    <div class="loading">
        <span>Helix is thinking...</span>
    </div>
    <div id="attachments-container"></div>
    <div id="input-container">
        <button id="attach-button" title="Attach files or folders">📎</button>
        <textarea id="message-input" placeholder="Ask Helix anything or drop files here..." rows="1"></textarea>
        <button id="send-button">Send</button>
    </div>

    <script>
        const vscode = acquireVsCodeApi();
        const chatContainer = document.getElementById('chat-container');
        const messageInput = document.getElementById('message-input');
        const sendButton = document.getElementById('send-button');
        const attachButton = document.getElementById('attach-button');
        const attachmentsContainer = document.getElementById('attachments-container');
        const dragOverlay = document.getElementById('drag-overlay');
        const loadingIndicator = document.querySelector('.loading');

        // Auto-resize textarea
        messageInput.addEventListener('input', () => {
            messageInput.style.height = 'auto';
            messageInput.style.height = messageInput.scrollHeight + 'px';
        });

        // Send message on Enter (Shift+Enter for new line)
        messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        sendButton.addEventListener('click', sendMessage);
        attachButton.addEventListener('click', () => {
            vscode.postMessage({ type: 'attachFiles' });
        });

        // Drag and drop handlers
        let dragCounter = 0;

        document.body.addEventListener('dragenter', (e) => {
            e.preventDefault();
            dragCounter++;
            if (dragCounter === 1) {
                dragOverlay.classList.add('visible');
                chatContainer.classList.add('drag-over');
            }
        });

        document.body.addEventListener('dragleave', (e) => {
            e.preventDefault();
            dragCounter--;
            if (dragCounter === 0) {
                dragOverlay.classList.remove('visible');
                chatContainer.classList.remove('drag-over');
            }
        });

        document.body.addEventListener('dragover', (e) => {
            e.preventDefault();
        });

        document.body.addEventListener('drop', (e) => {
            e.preventDefault();
            dragCounter = 0;
            dragOverlay.classList.remove('visible');
            chatContainer.classList.remove('drag-over');

            const files = Array.from(e.dataTransfer.files).map(f => f.path);
            if (files.length > 0) {
                vscode.postMessage({
                    type: 'filesDropped',
                    files: files
                });
            }
        });

        function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;

            vscode.postMessage({
                type: 'sendMessage',
                message: message
            });

            messageInput.value = '';
            messageInput.style.height = 'auto';
        }

        // Handle messages from extension
        window.addEventListener('message', event => {
            const message = event.data;

            switch (message.type) {
                case 'addMessage':
                    addMessage(message.role, message.content, message.agent, message.filesCreated, message.attachments);
                    break;
                case 'clearMessages':
                    clearMessages();
                    break;
                case 'setLoading':
                    setLoading(message.loading);
                    break;
                case 'updateAttachments':
                    updateAttachments(message.files);
                    break;
            }
        });

        function updateAttachments(files) {
            attachmentsContainer.innerHTML = '';
            
            if (files && files.length > 0) {
                attachmentsContainer.classList.add('visible');
                files.forEach(file => {
                    const chip = document.createElement('div');
                    chip.className = 'attachment-chip';
                    
                    const nameSpan = document.createElement('span');
                    nameSpan.className = 'attachment-name';
                    nameSpan.textContent = file.name;
                    nameSpan.title = file.path;
                    
                    const removeSpan = document.createElement('span');
                    removeSpan.className = 'attachment-remove';
                    removeSpan.textContent = '×';
                    removeSpan.onclick = () => {
                        vscode.postMessage({
                            type: 'removeAttachment',
                            path: file.path
                        });
                    };
                    
                    chip.appendChild(nameSpan);
                    chip.appendChild(removeSpan);
                    attachmentsContainer.appendChild(chip);
                });
            } else {
                attachmentsContainer.classList.remove('visible');
            }
        }

        function addMessage(role, content, agent, filesCreated, attachments) {
            // Remove empty state
            const emptyState = chatContainer.querySelector('.empty-state');
            if (emptyState) {
                emptyState.remove();
            }

            const messageDiv = document.createElement('div');
            messageDiv.className = \`message \${role}\`;

            const headerDiv = document.createElement('div');
            headerDiv.className = 'message-header';
            headerDiv.textContent = role === 'user' ? 'You' : (agent ? \`Helix (\${agent})\` : 'Helix');

            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.textContent = content;

            messageDiv.appendChild(headerDiv);
            messageDiv.appendChild(contentDiv);

            // Add attachments info for user messages
            if (role === 'user' && attachments && attachments.length > 0) {
                const attachmentDiv = document.createElement('div');
                attachmentDiv.className = 'attachment-info';
                attachmentDiv.textContent = \`📎 \${attachments.length} file(s) attached: \${attachments.map(a => a.name).join(', ')}\`;
                messageDiv.appendChild(attachmentDiv);
            }

            // Add files created badge
            if (filesCreated && filesCreated.length > 0) {
                const filesDiv = document.createElement('div');
                filesDiv.className = 'files-created';
                filesDiv.innerHTML = \`
                    <div class="files-created-title">📁 Files Created:</div>
                    \${filesCreated.map(f => \`<div>• \${f}</div>\`).join('')}
                \`;
                messageDiv.appendChild(filesDiv);
            }

            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        function clearMessages() {
            chatContainer.innerHTML = \`
                <div class="empty-state">
                    <div class="empty-state-icon">💬</div>
                    <div class="empty-state-title">Welcome to Helix AI</div>
                    <div class="empty-state-subtitle">Ask me anything about your code!</div>
                </div>
            \`;
        }

        function setLoading(loading) {
            loadingIndicator.classList.toggle('active', loading);
            sendButton.disabled = loading;
            messageInput.disabled = loading;
            
            if (loading) {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
        }
    </script>
</body>
</html>`;
    }
}
