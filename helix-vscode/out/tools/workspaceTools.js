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
exports.createFile = createFile;
exports.editFile = editFile;
exports.readFile = readFile;
exports.listFiles = listFiles;
exports.runCommand = runCommand;
exports.gitCommit = gitCommit;
exports.searchWorkspace = searchWorkspace;
exports.getWorkspaceContext = getWorkspaceContext;
const vscode = __importStar(require("vscode"));
const path = __importStar(require("path"));
/**
 * Create a new file in the workspace
 */
async function createFile(filePath, content) {
    try {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            return {
                success: false,
                message: 'No workspace folder open'
            };
        }
        const fullPath = vscode.Uri.joinPath(workspaceFolder.uri, filePath);
        const encoder = new TextEncoder();
        await vscode.workspace.fs.writeFile(fullPath, encoder.encode(content));
        return {
            success: true,
            message: `Created file: ${filePath}`,
            data: { path: filePath }
        };
    }
    catch (error) {
        return {
            success: false,
            message: `Failed to create file: ${error.message}`
        };
    }
}
/**
 * Edit an existing file by replacing old content with new content
 */
async function editFile(filePath, oldContent, newContent) {
    try {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            return {
                success: false,
                message: 'No workspace folder open'
            };
        }
        const fullPath = vscode.Uri.joinPath(workspaceFolder.uri, filePath);
        const document = await vscode.workspace.openTextDocument(fullPath);
        const editor = await vscode.window.showTextDocument(document);
        const text = document.getText();
        const startPos = text.indexOf(oldContent);
        if (startPos === -1) {
            return {
                success: false,
                message: `Could not find content to replace in ${filePath}`
            };
        }
        const endPos = startPos + oldContent.length;
        const startPosition = document.positionAt(startPos);
        const endPosition = document.positionAt(endPos);
        const range = new vscode.Range(startPosition, endPosition);
        await editor.edit(editBuilder => {
            editBuilder.replace(range, newContent);
        });
        await document.save();
        return {
            success: true,
            message: `Edited file: ${filePath}`,
            data: { path: filePath }
        };
    }
    catch (error) {
        return {
            success: false,
            message: `Failed to edit file: ${error.message}`
        };
    }
}
/**
 * Read the contents of a file in the workspace
 */
async function readFile(filePath) {
    try {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            return {
                success: false,
                message: 'No workspace folder open'
            };
        }
        const fullPath = vscode.Uri.joinPath(workspaceFolder.uri, filePath);
        const document = await vscode.workspace.openTextDocument(fullPath);
        const content = document.getText();
        return {
            success: true,
            message: `Read file: ${filePath}`,
            data: { path: filePath, content }
        };
    }
    catch (error) {
        return {
            success: false,
            message: `Failed to read file: ${error.message}`
        };
    }
}
/**
 * List files in the workspace matching a glob pattern
 */
async function listFiles(pattern = '**/*') {
    try {
        const files = await vscode.workspace.findFiles(pattern, '**/node_modules/**', 1000);
        const filePaths = files.map(file => vscode.workspace.asRelativePath(file));
        return {
            success: true,
            message: `Found ${filePaths.length} files`,
            data: { files: filePaths }
        };
    }
    catch (error) {
        return {
            success: false,
            message: `Failed to list files: ${error.message}`
        };
    }
}
/**
 * Execute a terminal command
 */
async function runCommand(command, cwd) {
    try {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        const workingDir = cwd
            ? path.join(workspaceFolder?.uri.fsPath || '', cwd)
            : workspaceFolder?.uri.fsPath;
        const terminal = vscode.window.createTerminal({
            name: 'Helix',
            cwd: workingDir
        });
        terminal.show();
        terminal.sendText(command);
        return {
            success: true,
            message: `Executing: ${command}`,
            data: { command, cwd: workingDir }
        };
    }
    catch (error) {
        return {
            success: false,
            message: `Failed to run command: ${error.message}`
        };
    }
}
/**
 * Create a git commit
 */
async function gitCommit(message, files) {
    try {
        const gitExtension = vscode.extensions.getExtension('vscode.git')?.exports;
        const git = gitExtension?.getAPI(1);
        if (!git || git.repositories.length === 0) {
            return {
                success: false,
                message: 'Git is not available or no repository found'
            };
        }
        const repo = git.repositories[0];
        // Stage files
        for (const file of files) {
            await repo.add([file]);
        }
        // Commit
        await repo.commit(message);
        return {
            success: true,
            message: `Created commit: ${message}`,
            data: { message, files }
        };
    }
    catch (error) {
        return {
            success: false,
            message: `Failed to create commit: ${error.message}`
        };
    }
}
/**
 * Search for text in workspace files
 */
async function searchWorkspace(query, filePattern) {
    try {
        const results = [];
        const files = await vscode.workspace.findFiles(filePattern || '**/*', '**/node_modules/**', 1000);
        for (const file of files) {
            try {
                const document = await vscode.workspace.openTextDocument(file);
                const text = document.getText();
                const lines = text.split('\n');
                lines.forEach((line, index) => {
                    if (line.includes(query)) {
                        results.push({
                            file: vscode.workspace.asRelativePath(file),
                            line: index + 1,
                            text: line.trim()
                        });
                    }
                });
            }
            catch (error) {
                // Skip files that can't be read
            }
        }
        return {
            success: true,
            message: `Found ${results.length} matches`,
            data: { results }
        };
    }
    catch (error) {
        return {
            success: false,
            message: `Failed to search workspace: ${error.message}`
        };
    }
}
/**
 * Get workspace context for agents
 */
async function getWorkspaceContext() {
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        return {};
    }
    const openFiles = vscode.workspace.textDocuments
        .filter(doc => !doc.isUntitled)
        .map(doc => vscode.workspace.asRelativePath(doc.uri));
    const activeFile = vscode.window.activeTextEditor
        ? vscode.workspace.asRelativePath(vscode.window.activeTextEditor.document.uri)
        : undefined;
    return {
        folder: workspaceFolder.uri.fsPath,
        openFiles,
        activeFile
    };
}
//# sourceMappingURL=workspaceTools.js.map