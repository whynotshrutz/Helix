"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const agentosClient_1 = require("./api/agentosClient");
const tools = __importStar(require("./tools/workspaceTools"));
let agentOSClient;
let serverTerminal;
function activate(context) {
    console.log('Helix AI Extension is now active!');
    // Initialize AgentOS client
    const config = vscode.workspace.getConfiguration('helix');
    const serverUrl = config.get('serverUrl') || 'http://localhost:7777';
    agentOSClient = new agentosClient_1.AgentOSClient(serverUrl);
    // Register chat participants for each agent
    const agents = [
        { id: 'planner', name: 'Helix Planner', description: 'Analyzes prompts and creates execution plans' },
        { id: 'coder', name: 'Helix Coder', description: 'Generates and modifies code' },
        { id: 'tester', name: 'Helix Tester', description: 'Creates and runs tests' },
        { id: 'reviewer', name: 'Helix Reviewer', description: 'Reviews code changes and ensures quality' },
        { id: 'explainer', name: 'Helix Explainer', description: 'Generates human-readable explanations' }
    ];
    agents.forEach(agent => {
        const participant = vscode.chat.createChatParticipant(`helix.${agent.id}`, async (request, chatContext, stream, token) => {
            return await handleChatRequest(agent.id, agent.name, request, chatContext, stream, token);
        });
        participant.iconPath = vscode.Uri.joinPath(context.extensionUri, 'media', `${agent.id}-icon.png`);
        context.subscriptions.push(participant);
    });
    // Register commands
    context.subscriptions.push(vscode.commands.registerCommand('helix.startServer', startServer), vscode.commands.registerCommand('helix.stopServer', stopServer), vscode.commands.registerCommand('helix.showPreview', showPreview), vscode.commands.registerCommand('helix.runWorkflow', runWorkflow), vscode.commands.registerCommand('helix.selectAgent', selectAgent));
    // Check server status
    checkServerStatus();
    // Auto-start server if configured
    if (config.get('autoStart')) {
        startServer();
    }
}
async function handleChatRequest(agentId, agentName, request, chatContext, stream, token) {
    try {
        stream.progress(`${agentName} is thinking...`);
        // Get workspace context
        const workspaceContext = await tools.getWorkspaceContext();
        // Send request to AgentOS
        const response = await agentOSClient.chat(agentId, request.prompt, {
            sessionId: generateSessionId(chatContext),
            workspace: workspaceContext
        });
        // Stream response text
        if (response.content) {
            stream.markdown(response.content);
        }
        // Execute tool calls from agent
        if (response.tool_calls && response.tool_calls.length > 0) {
            for (const toolCall of response.tool_calls) {
                stream.progress(`Executing ${toolCall.tool}...`);
                const result = await executeTool(toolCall.tool, toolCall.parameters, stream);
                if (result.success) {
                    stream.markdown(`\n\n✅ ${result.message}`);
                }
                else {
                    stream.markdown(`\n\n❌ ${result.message}`);
                }
            }
        }
    }
    catch (error) {
        if (error.message.includes('not running')) {
            stream.markdown('❌ **AgentOS server is not running.**\n\n');
            stream.markdown('Please start the server:\n');
            stream.button({
                command: 'helix.startServer',
                title: 'Start AgentOS Server'
            });
        }
        else {
            stream.markdown(`❌ Error: ${error.message}`);
        }
    }
}
async function executeTool(tool, parameters, stream) {
    let result;
    switch (tool) {
        case 'createFile':
        case 'create_file':
            result = await tools.createFile(parameters.path, parameters.content);
            if (result.success) {
                stream.button({
                    command: 'vscode.open',
                    title: 'Open File',
                    arguments: [vscode.Uri.file(parameters.path)]
                });
            }
            break;
        case 'editFile':
        case 'edit_file':
            result = await tools.editFile(parameters.path, parameters.old_content || parameters.oldContent, parameters.new_content || parameters.newContent);
            if (result.success) {
                stream.button({
                    command: 'vscode.open',
                    title: 'View Changes',
                    arguments: [vscode.Uri.file(parameters.path)]
                });
            }
            break;
        case 'readFile':
        case 'read_workspace_file':
            result = await tools.readFile(parameters.path);
            if (result.success && result.data) {
                stream.markdown(`\n\n\`\`\`\n${result.data.content}\n\`\`\``);
            }
            break;
        case 'listFiles':
        case 'list_workspace_files':
            result = await tools.listFiles(parameters.pattern);
            if (result.success && result.data) {
                stream.markdown(`\n\nFiles found:\n${result.data.files.slice(0, 20).join('\n')}`);
                if (result.data.files.length > 20) {
                    stream.markdown(`\n\n... and ${result.data.files.length - 20} more`);
                }
            }
            break;
        case 'runCommand':
        case 'run_command':
            result = await tools.runCommand(parameters.command, parameters.cwd);
            break;
        case 'gitCommit':
        case 'git_commit':
            result = await tools.gitCommit(parameters.message, parameters.files);
            break;
        case 'searchWorkspace':
        case 'search_workspace':
            result = await tools.searchWorkspace(parameters.query, parameters.file_pattern);
            if (result.success && result.data) {
                const matches = result.data.results.slice(0, 10);
                stream.markdown(`\n\nSearch results:\n`);
                matches.forEach((match) => {
                    stream.markdown(`- ${match.file}:${match.line} - ${match.text}\n`);
                });
                if (result.data.results.length > 10) {
                    stream.markdown(`\n... and ${result.data.results.length - 10} more matches`);
                }
            }
            break;
        case 'showPreview':
        case 'show_preview':
            result = { success: true, message: 'Preview feature coming soon!' };
            stream.button({
                command: 'helix.showPreview',
                title: 'Show Preview'
            });
            break;
        default:
            result = {
                success: false,
                message: `Unknown tool: ${tool}`
            };
    }
    return result;
}
function startServer() {
    const config = vscode.workspace.getConfiguration('helix');
    const pythonPath = config.get('pythonPath') || 'python';
    // Find workspace root where helix is installed
    const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    if (!workspaceRoot) {
        vscode.window.showErrorMessage('No workspace folder open');
        return;
    }
    // Create terminal for server
    serverTerminal = vscode.window.createTerminal({
        name: 'Helix AgentOS',
        cwd: workspaceRoot
    });
    serverTerminal.show();
    // Start the server
    serverTerminal.sendText(`${pythonPath} -m helix --serve`);
    vscode.window.showInformationMessage('🚀 Starting Helix AgentOS Server...', 'View Terminal').then(selection => {
        if (selection === 'View Terminal' && serverTerminal) {
            serverTerminal.show();
        }
    });
    // Check server status after a delay
    setTimeout(() => checkServerStatus(), 5000);
}
function stopServer() {
    if (serverTerminal) {
        serverTerminal.dispose();
        serverTerminal = undefined;
        vscode.window.showInformationMessage('Helix AgentOS Server stopped');
    }
    else {
        vscode.window.showWarningMessage('No server terminal found');
    }
}
async function checkServerStatus() {
    try {
        const isHealthy = await agentOSClient.health();
        if (isHealthy) {
            vscode.window.showInformationMessage('✅ Helix AgentOS is running');
        }
        else {
            const action = await vscode.window.showWarningMessage('⚠️ Helix AgentOS is not responding', 'Start Server');
            if (action === 'Start Server') {
                startServer();
            }
        }
    }
    catch (error) {
        const action = await vscode.window.showWarningMessage('❌ Helix AgentOS is not running', 'Start Server');
        if (action === 'Start Server') {
            startServer();
        }
    }
}
function showPreview() {
    vscode.window.showInformationMessage('Preview feature coming in the next update!');
    // TODO: Implement webview preview panel
}
async function runWorkflow() {
    const prompt = await vscode.window.showInputBox({
        prompt: 'What would you like to build?',
        placeHolder: 'e.g., Create a calculator app with tests'
    });
    if (prompt) {
        // Open chat with planner
        await vscode.commands.executeCommand('workbench.action.chat.open', {
            query: `@helix-planner ${prompt}`
        });
    }
}
async function selectAgent() {
    const agents = [
        { label: '$(search) Planner', description: 'Analyzes prompts and creates execution plans', id: 'planner' },
        { label: '$(code) Coder', description: 'Generates and modifies code', id: 'coder' },
        { label: '$(beaker) Tester', description: 'Creates and runs tests', id: 'tester' },
        { label: '$(check) Reviewer', description: 'Reviews code changes and ensures quality', id: 'reviewer' },
        { label: '$(book) Explainer', description: 'Generates human-readable explanations', id: 'explainer' }
    ];
    const selection = await vscode.window.showQuickPick(agents, {
        placeHolder: 'Select an agent to chat with'
    });
    if (selection) {
        await vscode.commands.executeCommand('workbench.action.chat.open', {
            query: `@helix-${selection.id} `
        });
    }
}
function generateSessionId(chatContext) {
    // Use VS Code's chat history to maintain session continuity
    return `vscode-${chatContext.history.length}-${Date.now()}`;
}
function deactivate() {
    if (serverTerminal) {
        serverTerminal.dispose();
    }
}
//# sourceMappingURL=extension.js.map