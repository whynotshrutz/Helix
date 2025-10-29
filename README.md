# Helix Multi-Agent System

Helix is a multi-agent AI platform that integrates with VS Code and the web, enabling collaborative code generation, planning, testing, reviewing, and explanation by specialized agents. It is powered by NVIDIA NIM and supports extensibility for advanced workflows.

## Features

- **Multi-Agent Collaboration:** Planner, Coder, Tester, Reviewer, and Explainer agents work together on your codebase.
- **VS Code Extension:** Interact with agents directly in VS Code via a custom chat panel and sidebar.
- **Web UI:** Full-featured web interface for agent chat, file management, and workflow orchestration.
- **API Access:** RESTful endpoints for integrating Helix with other tools and automations.
- **NVIDIA NIM Integration:** Uses Llama 3.1 and other models for high-quality code and reasoning.
- **Azure-Aware:** (If enabled) Follows Azure best practices and planning rules for Azure-related tasks.

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/helix.git
cd helix
```

### 2. Set Up Environment

Create a `.env` file in the root directory:

```env
NIM_API_KEY=your_nvidia_api_key
NVIDIA_API_KEY=your_nvidia_api_key
NIM_BASE_URL=https://integrate.api.nvidia.com/v1
```

> **Note:** You can get your NVIDIA API key from [NVIDIA Build](https://build.nvidia.com).

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the AgentOS Server

```bash
python -m helix --serve
```

The server will start on `http://localhost:7777`.

### 5. Use the Web UI

Open your browser and go to:  
[http://localhost:7777](http://localhost:7777)

### 6. VS Code Extension (Standalone)

1. Go to the `helix-vscode` directory.
2. Install dependencies and build:
    ```bash
    npm install
    npm run build
    ```
3. Package and install the extension:
    ```bash
    npx vsce package
    code --install-extension helix-ai-standalone-2.0.0.vsix
    ```
4. Open VS Code, press `Ctrl+Shift+P`, and run `Helix: Open Chat`.

## Usage

- **Chat with Agents:** Ask for code, plans, tests, reviews, or explanations.
- **File Operations:** Agents can create, edit, and review files in your workspace.
- **API Integration:** Use REST endpoints for automation or integration with other tools.

## Azure Integration

If you work with Azure, Helix can:
- Use Azure best practices for code generation and deployment.
- Plan and explain Azure Functions and Static Web Apps before editing files.
- Summarize Azure topics and recommend custom modes.

> **Note:** Azure-specific features require the relevant tools and configuration.

## Contributing

1. Fork the repo and create your branch.
2. Commit your changes.
3. Push to your fork and submit a pull request.

## License

[MIT License](LICENSE)

---

**Helix** – AI agents for your code, your workflow, your way.
