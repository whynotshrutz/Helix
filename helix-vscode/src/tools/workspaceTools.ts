import * as vscode from 'vscode';
import * as path from 'path';

export interface ToolResult {
    success: boolean;
    message: string;
    data?: any;
}

/**
 * Create a new file in the workspace
 */
export async function createFile(filePath: string, content: string): Promise<ToolResult> {
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
    } catch (error: any) {
        return {
            success: false,
            message: `Failed to create file: ${error.message}`
        };
    }
}

/**
 * Edit an existing file by replacing old content with new content
 */
export async function editFile(
    filePath: string,
    oldContent: string,
    newContent: string
): Promise<ToolResult> {
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
    } catch (error: any) {
        return {
            success: false,
            message: `Failed to edit file: ${error.message}`
        };
    }
}

/**
 * Read the contents of a file in the workspace
 */
export async function readFile(filePath: string): Promise<ToolResult> {
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
    } catch (error: any) {
        return {
            success: false,
            message: `Failed to read file: ${error.message}`
        };
    }
}

/**
 * List files in the workspace matching a glob pattern
 */
export async function listFiles(pattern: string = '**/*'): Promise<ToolResult> {
    try {
        const files = await vscode.workspace.findFiles(
            pattern,
            '**/node_modules/**',
            1000
        );

        const filePaths = files.map(file => 
            vscode.workspace.asRelativePath(file)
        );

        return {
            success: true,
            message: `Found ${filePaths.length} files`,
            data: { files: filePaths }
        };
    } catch (error: any) {
        return {
            success: false,
            message: `Failed to list files: ${error.message}`
        };
    }
}

/**
 * Execute a terminal command
 */
export async function runCommand(
    command: string,
    cwd?: string
): Promise<ToolResult> {
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
    } catch (error: any) {
        return {
            success: false,
            message: `Failed to run command: ${error.message}`
        };
    }
}

/**
 * Create a git commit
 */
export async function gitCommit(
    message: string,
    files: string[]
): Promise<ToolResult> {
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
    } catch (error: any) {
        return {
            success: false,
            message: `Failed to create commit: ${error.message}`
        };
    }
}

/**
 * Search for text in workspace files
 */
export async function searchWorkspace(
    query: string,
    filePattern?: string
): Promise<ToolResult> {
    try {
        const results: Array<{ file: string; line: number; text: string }> = [];

        const files = await vscode.workspace.findFiles(
            filePattern || '**/*',
            '**/node_modules/**',
            1000
        );

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
            } catch (error) {
                // Skip files that can't be read
            }
        }

        return {
            success: true,
            message: `Found ${results.length} matches`,
            data: { results }
        };
    } catch (error: any) {
        return {
            success: false,
            message: `Failed to search workspace: ${error.message}`
        };
    }
}

/**
 * Get workspace context for agents
 */
export async function getWorkspaceContext(): Promise<any> {
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
