/**
 * Helix AI Extension - Standalone Version
 * No dependency on GitHub Copilot Chat - uses custom Webview Panel
 */

import * as vscode from 'vscode';
import { AgentOSClient } from './api/agentosClient';
import * as workspaceTools from './tools/workspaceTools';

// Extension state
let chatPanel: vscode.WebviewPanel | undefined;
let agentosClient: AgentOSClient;
let currentAgent: string = 'coder';
let serverProcess: any;

export function activate(context: vscode.ExtensionContext) {
    console.log('Helix AI Extension (Standalone) is activating...');

    // Initialize AgentOS client
    const config = vscode.workspace.getConfiguration('helix');
    const serverUrl = config.get<string>('serverUrl', 'http://localhost:7777');
    agentosClient = new AgentOSClient(serverUrl);

    // Register Tree View for agent selection
    const agentsProvider = new AgentsTreeProvider();
    vscode.window.registerTreeDataProvider('helix-agents', agentsProvider);

    // Register commands
    context.subscriptions.push(
        // Main chat command
        vscode.commands.registerCommand('helix.openChat', () => {
            openChatPanel(context);
        }),

        // Agent selection commands
        vscode.commands.registerCommand('helix.selectAgent', async () => {
            const agents = ['planner', 'coder', 'tester', 'reviewer', 'explainer'];
            const selected = await vscode.window.showQuickPick(agents.map(a => ({
                label: a.charAt(0).toUpperCase() + a.slice(1),
                description: getAgentDescription(a),
                value: a
            })), {
                placeHolder: 'Select an agent'
            });

            if (selected) {
                currentAgent = selected.value;
                agentsProvider.refresh();
                if (chatPanel) {
                    chatPanel.webview.postMessage({
                        type: 'agentChanged',
                        agent: currentAgent
                    });
                }
                vscode.window.showInformationMessage(`Switched to ${selected.label} agent`);
            }
        }),

        // Individual agent commands
        vscode.commands.registerCommand('helix.chatWithPlanner', () => {
            currentAgent = 'planner';
            agentsProvider.refresh();
            openChatPanel(context);
        }),
        vscode.commands.registerCommand('helix.chatWithCoder', () => {
            currentAgent = 'coder';
            agentsProvider.refresh();
            openChatPanel(context);
        }),
        vscode.commands.registerCommand('helix.chatWithTester', () => {
            currentAgent = 'tester';
            agentsProvider.refresh();
            openChatPanel(context);
        }),
        vscode.commands.registerCommand('helix.chatWithReviewer', () => {
            currentAgent = 'reviewer';
            agentsProvider.refresh();
            openChatPanel(context);
        }),
        vscode.commands.registerCommand('helix.chatWithExplainer', () => {
            currentAgent = 'explainer';
            agentsProvider.refresh();
            openChatPanel(context);
        }),

        // Server management
        vscode.commands.registerCommand('helix.startServer', async () => {
            await startServer();
        }),
        vscode.commands.registerCommand('helix.stopServer', async () => {
            await stopServer();
        }),
        vscode.commands.registerCommand('helix.checkServer', async () => {
            await checkServerStatus();
        })
    );

    // Auto-start server if configured
    if (config.get<boolean>('autoStart', false)) {
        startServer();
    }

    console.log('Helix AI Extension activated successfully!');
}

export function deactivate() {
    if (serverProcess) {
        stopServer();
    }
}

/**
 * Open or focus the chat panel
 */
function openChatPanel(context: vscode.ExtensionContext) {
    if (chatPanel) {
        chatPanel.reveal();
        return;
    }

    chatPanel = vscode.window.createWebviewPanel(
        'helixChat',
        `Helix AI - ${currentAgent.charAt(0).toUpperCase() + currentAgent.slice(1)}`,
        vscode.ViewColumn.Beside,
        {
            enableScripts: true,
            retainContextWhenHidden: true,
            localResourceRoots: [vscode.Uri.joinPath(context.extensionUri, 'media')]
        }
    );

    chatPanel.webview.html = getWebviewContent(chatPanel.webview, context);

    // Handle messages from webview
    chatPanel.webview.onDidReceiveMessage(
        async message => {
            await handleWebviewMessage(message);
        },
        undefined,
        context.subscriptions
    );

    chatPanel.onDidDispose(() => {
        chatPanel = undefined;
    });

    // Send initial state
    chatPanel.webview.postMessage({
        type: 'initialize',
        agent: currentAgent
    });
}

/**
 * Handle messages from the webview
 */
async function handleWebviewMessage(message: any) {
    switch (message.type) {
        case 'sendMessage':
            await handleUserMessage(message.text, message.agent);
            break;

        case 'executeCommand':
            await executeCommand(message.command);
            break;

        case 'createFile':
            await workspaceTools.createFile(message.path, message.content);
            sendWebviewMessage({ type: 'fileCreated', path: message.path });
            break;

        case 'editFile':
            await workspaceTools.editFile(message.path, message.oldContent, message.newContent);
            sendWebviewMessage({ type: 'fileEdited', path: message.path });
            break;

        case 'readFile':
            const content = await workspaceTools.readFile(message.path);
            sendWebviewMessage({ type: 'fileContent', path: message.path, content });
            break;

        case 'listFiles':
            const files = await workspaceTools.listFiles(message.pattern);
            sendWebviewMessage({ type: 'fileList', files });
            break;
    }
}

/**
 * Handle user message and get agent response
 */
async function handleUserMessage(text: string, agent: string) {
    try {
        // Show loading state
        sendWebviewMessage({
            type: 'agentThinking',
            agent
        });

        // Get workspace context
        const context = await workspaceTools.getWorkspaceContext();

        // Send to agent
        const response = await agentosClient.chat(agent, text, {
            sessionId: `vscode-${agent}-${Date.now()}`,
            workspace: context
        });

        // Extract content
        const content = response.content || '';

        // Send response back to webview
        sendWebviewMessage({
            type: 'agentResponse',
            agent,
            content,
            timestamp: new Date().toISOString()
        });

        // Check for tool calls and execute them
        await handleToolCalls(response);

    } catch (error: any) {
        sendWebviewMessage({
            type: 'error',
            message: error.message || 'Failed to get response from agent'
        });
    }
}

/**
 * Handle tool calls from agent response
 */
async function handleToolCalls(response: any) {
    // Simple tool extraction from response
    // Look for tool calls in the response content
    const content = response.content || '';
    
    // For now, we'll skip automatic tool execution
    // Tools will be executed manually through webview messages
    // In future, we can parse structured tool calls from the agent
}

/**
 * Send message to webview
 */
function sendWebviewMessage(message: any) {
    if (chatPanel) {
        chatPanel.webview.postMessage(message);
    }
}

/**
 * Execute a command in terminal
 */
async function executeCommand(command: string) {
    const terminal = vscode.window.createTerminal('Helix Command');
    terminal.show();
    terminal.sendText(command);
}

/**
 * Start AgentOS server
 */
async function startServer() {
    const config = vscode.workspace.getConfiguration('helix');
    const pythonPath = config.get<string>('pythonPath', 'python');

    const terminal = vscode.window.createTerminal({
        name: 'Helix Server',
        hideFromUser: false
    });

    terminal.show();
    terminal.sendText(`${pythonPath} -m helix --serve`);

    vscode.window.showInformationMessage('Starting Helix AgentOS server...');
}

/**
 * Stop AgentOS server
 */
async function stopServer() {
    // For now, just show message - user can close terminal manually
    vscode.window.showInformationMessage('Please close the "Helix Server" terminal to stop the server');
}

/**
 * Check server status
 */
async function checkServerStatus() {
    try {
        const health = await agentosClient.health();
        vscode.window.showInformationMessage(`Server is running: ${JSON.stringify(health)}`);
    } catch (error) {
        vscode.window.showWarningMessage('Server is not running. Start it with "Helix: Start Server"');
    }
}

/**
 * Get agent description
 */
function getAgentDescription(agent: string): string {
    const descriptions: { [key: string]: string } = {
        planner: 'Creates execution plans and analyzes requirements',
        coder: 'Generates and modifies code',
        tester: 'Creates tests and runs quality checks',
        reviewer: 'Reviews code for quality and security',
        explainer: 'Generates documentation and explanations'
    };
    return descriptions[agent] || '';
}

/**
 * Tree Data Provider for Agents
 */
class AgentsTreeProvider implements vscode.TreeDataProvider<AgentTreeItem> {
    private _onDidChangeTreeData = new vscode.EventEmitter<AgentTreeItem | undefined>();
    readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

    refresh(): void {
        this._onDidChangeTreeData.fire(undefined);
    }

    getTreeItem(element: AgentTreeItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: AgentTreeItem): AgentTreeItem[] {
        if (!element) {
            // Root level - show all agents
            return [
                new AgentTreeItem('planner', 'Planner', 'Creates execution plans', 'planner' === currentAgent),
                new AgentTreeItem('coder', 'Coder', 'Generates code', 'coder' === currentAgent),
                new AgentTreeItem('tester', 'Tester', 'Runs tests', 'tester' === currentAgent),
                new AgentTreeItem('reviewer', 'Reviewer', 'Reviews code', 'reviewer' === currentAgent),
                new AgentTreeItem('explainer', 'Explainer', 'Writes documentation', 'explainer' === currentAgent)
            ];
        }
        return [];
    }
}

/**
 * Tree Item for Agent
 */
class AgentTreeItem extends vscode.TreeItem {
    constructor(
        public readonly id: string,
        public readonly label: string,
        public readonly agentDescription: string,
        private isActive: boolean
    ) {
        super(label, vscode.TreeItemCollapsibleState.None);
        this.tooltip = agentDescription;
        this.description = agentDescription;
        this.command = {
            command: `helix.chatWith${label}`,
            title: `Chat with ${label}`,
            arguments: []
        };

        if (isActive) {
            this.iconPath = new vscode.ThemeIcon('account', new vscode.ThemeColor('charts.green'));
        } else {
            this.iconPath = new vscode.ThemeIcon('circle-outline');
        }
    }
}

/**
 * Get webview HTML content
 */
function getWebviewContent(webview: vscode.Webview, context: vscode.ExtensionContext): string {
    const htmlPath = vscode.Uri.joinPath(context.extensionUri, 'media', 'chat.html');
    const fs = require('fs');
    const htmlContent = fs.readFileSync(htmlPath.fsPath, 'utf8');
    return htmlContent;
}
