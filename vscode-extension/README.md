# Helix VS Code extension (MCP client scaffold)

This is a minimal scaffold for a VS Code extension that acts as a frontend to the Helix backend.

It registers two commands:

- `Helix: Chat` — opens an input box, sends prompt to backend `/run`, shows response in Output panel.
- `Helix: Inline Suggest` — requests an inline completion for current line and shows suggestion as a quick pick (demo).

This is a starting point. For a production MCP client, implement the real MCP transport and streaming support (streamable-http / SSE / stdio).
