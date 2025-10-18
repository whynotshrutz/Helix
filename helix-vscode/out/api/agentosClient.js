"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.AgentOSClient = void 0;
const axios_1 = __importDefault(require("axios"));
class AgentOSClient {
    constructor(baseURL = 'http://localhost:7777') {
        this.baseURL = baseURL;
        this.client = axios_1.default.create({
            baseURL,
            headers: {
                'Content-Type': 'application/json'
            },
            timeout: 120000 // 2 minutes for long-running agent tasks
        });
    }
    /**
     * Check if AgentOS server is running
     */
    async health() {
        try {
            const response = await this.client.get('/vscode/health');
            return response.data.status === 'ok';
        }
        catch (error) {
            return false;
        }
    }
    /**
     * List all available agents
     */
    async listAgents() {
        try {
            const response = await this.client.get('/agents');
            const agents = response.data;
            // Handle different response formats
            if (Array.isArray(agents)) {
                return agents.map((agent) => ({
                    id: agent.id || agent.name?.toLowerCase(),
                    name: agent.name,
                    description: agent.description || ''
                }));
            }
            return [];
        }
        catch (error) {
            console.error('Failed to list agents:', error);
            throw error;
        }
    }
    /**
     * Chat with a specific agent
     */
    async chat(agentId, message, options = {}) {
        try {
            // Update workspace context if provided
            if (options.workspace) {
                await this.updateWorkspaceContext(options.workspace);
            }
            // Send chat request to agent
            const response = await this.client.post(`/agents/${agentId}/runs`, {
                message: message,
                session_id: options.sessionId || this.generateSessionId(),
                stream: options.stream || false
            });
            const data = response.data;
            // Parse response
            return {
                content: data.content || data.response || '',
                messages: data.messages || [],
                tool_calls: this.extractToolCalls(data)
            };
        }
        catch (error) {
            console.error(`Failed to chat with agent ${agentId}:`, error);
            // Provide helpful error messages
            if (error.response?.status === 404) {
                throw new Error(`Agent "${agentId}" not found. Available agents: planner, coder, tester, reviewer, explainer`);
            }
            throw error;
        }
    }
    /**
     * Stream chat response from agent
     */
    async *chatStream(agentId, message, options = {}) {
        try {
            // Update workspace context if provided
            if (options.workspace) {
                await this.updateWorkspaceContext(options.workspace);
            }
            const response = await this.client.post(`/agents/${agentId}/runs`, {
                message: message,
                session_id: options.sessionId || this.generateSessionId(),
                stream: true
            }, {
                responseType: 'stream'
            });
            // Parse streaming response
            const stream = response.data;
            let buffer = '';
            for await (const chunk of stream) {
                buffer += chunk.toString();
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';
                for (const line of lines) {
                    if (line.trim()) {
                        try {
                            const data = JSON.parse(line);
                            yield {
                                content: data.content || data.delta || '',
                                tool_calls: this.extractToolCalls(data)
                            };
                        }
                        catch (e) {
                            // Skip invalid JSON
                        }
                    }
                }
            }
        }
        catch (error) {
            console.error(`Failed to stream chat with agent ${agentId}:`, error);
            throw error;
        }
    }
    /**
     * Update workspace context for agents
     */
    async updateWorkspaceContext(context) {
        try {
            await this.client.post('/vscode/workspace-context', {
                workspace_folder: context.folder,
                open_files: context.openFiles,
                active_file: context.activeFile,
                file_contents: context.fileContents
            });
        }
        catch (error) {
            console.error('Failed to update workspace context:', error);
            // Don't throw - this is not critical
        }
    }
    /**
     * Execute a tool action
     */
    async executeTool(tool, parameters, agentId) {
        try {
            const response = await this.client.post('/vscode/execute-tool', {
                tool,
                parameters,
                agent_id: agentId
            });
            return response.data;
        }
        catch (error) {
            console.error(`Failed to execute tool ${tool}:`, error);
            throw error;
        }
    }
    /**
     * Extract tool calls from agent response
     */
    extractToolCalls(data) {
        const toolCalls = [];
        // Check different response formats
        if (data.tool_calls && Array.isArray(data.tool_calls)) {
            return data.tool_calls;
        }
        // Check for function calls
        if (data.function_call) {
            toolCalls.push({
                tool: data.function_call.name,
                parameters: JSON.parse(data.function_call.arguments || '{}')
            });
        }
        // Check for actions
        if (data.action) {
            toolCalls.push({
                tool: data.action,
                parameters: data.params || data.parameters || {}
            });
        }
        return toolCalls;
    }
    /**
     * Generate a unique session ID
     */
    generateSessionId() {
        return `vscode-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    }
    /**
     * Get server status
     */
    async getStatus() {
        try {
            const response = await this.client.get('/');
            return response.data;
        }
        catch (error) {
            throw new Error('AgentOS server is not running');
        }
    }
}
exports.AgentOSClient = AgentOSClient;
//# sourceMappingURL=agentosClient.js.map