#!/usr/bin/env node
// Dev-only launcher for local checkout.
// Production MCP uses uvx directly (see references/mcp_config_template.json).
const { spawnSync } = require('child_process');
const path = require('path');
const fs = require('fs');

/**
 * Jira Daily PM Radar - MCP Launcher
 * 
 * Runs the MCP server using `uv run` from the project directory.
 * Requires JIRA_RADAR_PROJECT_DIR environment variable to be set.
 */

let projectDir = process.env.JIRA_RADAR_PROJECT_DIR;

// Fallback: try to find .install-meta.json for backward compatibility
if (!projectDir) {
  const homeDir = process.env.USERPROFILE || process.env.HOME || '';
  const skillName = 'jira-daily-pm-radar';
  const candidateDirs = [
    path.join(homeDir, '.claude', 'skills', skillName),
    path.join(homeDir, '.gemini', 'skills', skillName),
    path.join(homeDir, '.agents', 'skills', skillName),
  ];

  for (const dir of candidateDirs) {
    const p = path.join(dir, '.install-meta.json');
    if (fs.existsSync(p)) {
      try {
        const meta = JSON.parse(fs.readFileSync(p, 'utf8'));
        if (meta && meta.project_dir) {
          projectDir = meta.project_dir;
          break;
        }
      } catch (e) {
        // ignore errors in fallback
      }
    }
  }
}

// Second fallback: if launched from bin/ within the repo
if (!projectDir) {
  const scriptDir = __dirname;
  const rootDir = path.join(scriptDir, '..');
  if (fs.existsSync(path.join(rootDir, 'pyproject.toml'))) {
    projectDir = rootDir;
  }
}

if (!projectDir) {
  console.error("Error: JIRA_RADAR_PROJECT_DIR environment variable is not set.");
  console.error("Set it to the absolute path of the cloned jira-daily-pm-radar repository.");
  process.exit(1);
}

if (!fs.existsSync(projectDir)) {
  console.error("Error: Project directory does not exist: " + projectDir);
  process.exit(1);
}

// Use uv run --directory <project_dir> --extra mcp jira-radar-mcp
const result = spawnSync('uv', ['run', '--directory', projectDir, '--extra', 'mcp', 'jira-radar-mcp'], {
  stdio: 'inherit',
  shell: true
});

if (result.error) {
  console.error("Failed to start uv:", result.error);
  process.exit(1);
}

process.exit(result.status || 0);
