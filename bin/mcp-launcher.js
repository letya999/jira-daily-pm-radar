#!/usr/bin/env node
const { spawnSync } = require('child_process');

console.error("Starting Jira Daily PM Radar MCP via uvx...");

const result = spawnSync('uvx', ['jira-daily-pm-radar', 'mcp'], {
  stdio: 'inherit',
  shell: true
});

if (result.error) {
  console.error("Failed to start uvx:", result.error);
  process.exit(1);
}

process.exit(result.status || 0);
