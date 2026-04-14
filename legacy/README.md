# Legacy

This folder contains the original MCP server + cloud deployment code (Cloudflare Worker, Railway, Fly.io, Poke AI integration). It worked but is **no longer maintained** or deployed.

The project's headline is now the Claude Code Skill at [../skills/](../skills/) — a local-first, offline vector search over Apple Notes. The skill replaces the need for the hosted MCP service.

If you want to run the MCP server locally, the core files are still in the parent directory (`scripts/indexer.py`, `scripts/server.py`, `requirements.txt`). The deployment recipes in this folder are kept for reference only.
