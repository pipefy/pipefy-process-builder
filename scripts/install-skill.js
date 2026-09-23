#!/usr/bin/env node
'use strict'

// Runs as this package's postinstall: copies the skill files into the
// Claude Code skills directory so `npm install` alone is enough.
//
// - Global install (`npm install -g` / `npm i -g`): npm sets
//   npm_config_global=true, and there is no "project" to anchor to, so
//   the target is the global skills directory (~/.claude/skills/).
// - Local/project install: npm runs this script with cwd set to this
//   package's own folder inside node_modules, so INIT_CWD (the directory
//   the user actually ran `npm install` from) is what locates the
//   project's .claude/skills/, not process.cwd().

const fs = require('fs')
const os = require('os')
const path = require('path')

const SKILL_NAME = 'pipefy-process-builder'
const FILES_TO_COPY = ['SKILL.md', 'references', 'perks']

const packageRoot = path.resolve(__dirname, '..')
const isGlobal = process.env.npm_config_global === 'true'
const projectRoot = process.env.INIT_CWD || process.cwd()
const targetDir = path.join(
  isGlobal ? os.homedir() : projectRoot,
  '.claude',
  'skills',
  SKILL_NAME
)

try {
  fs.mkdirSync(targetDir, { recursive: true })
  for (const name of FILES_TO_COPY) {
    const src = path.join(packageRoot, name)
    const dest = path.join(targetDir, name)
    // Remove the previous copy first: cpSync only merges/overwrites, it
    // never deletes -- without this, a file dropped between versions
    // would linger in dest forever, stale and out of sync with SKILL.md.
    fs.rmSync(dest, { recursive: true, force: true })
    if (fs.existsSync(src)) {
      fs.cpSync(src, dest, { recursive: true })
    }
  }
  console.log(`[${SKILL_NAME}] skill installed to ${targetDir}`)
} catch (err) {
  console.warn(`[${SKILL_NAME}] could not auto-install skill files: ${err.message}`)
  console.warn(`[${SKILL_NAME}] copy SKILL.md, references/, and perks/ into ${targetDir} manually`)
}
