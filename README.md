# Zscaler AI Guard Domain Sync

Zscaler AI Guard requires ZIA to intercept and forward specific Generative AI traffic to its inspection engines. This requires maintaining an up-to-date **IP Destination Group** containing all FQDNs for supported AI providers (like OpenAI, Anthropic, Google Gemini, etc.).

Because Zscaler continuously adds support for new AI applications, the required domains change over time. This tool actively scrapes the [Zscaler Help Portal](https://help.zscaler.com/secure-ai-users/integrating-zia-ai-guard), formats the newly discovered domains, and pushes them seamlessly to your live Zscaler ZIA tenant via the OneAPI.

## Features
- **Zero-Dependency Web Scraping:** Uses native Python libraries to extract the raw JSON backing the React.js Zscaler Help Portal, completely bypassing the need for a headless browser (like Selenium or Puppeteer).
- **Automated Formatting:** Pre-processes top-level domains (e.g., `.perplexity.ai` is automatically reformatted into a valid ZIA wildcard `*.perplexity.ai`).
- **Fully Idempotent:** If the target IP Destination Group doesn't exist, it creates it. If it does exist, it updates it via a complete override.
- **Auto-Activation:** Triggers a ZIA configuration activation command (`POST /status/activate`) instantly after applying changes.

---

## ⚙️ Quick Installation (Gemini CLI)

### Install globally under your user account:
```bash
gemini skills install https://github.com/hshen-ai/zscaler-aiguard-domain-sync.git
```

### Enable the skill in your active session:
```bash
/skills reload
```

---

## 🤖 Multi-Agent Compatibility (Gemini CLI, Claude Code, Cursor, Copilot)

While this skill was natively designed, packaged, and tested on **Gemini CLI**, its modular and self-contained structure (comprising standard Markdown instructions and parameter-driven Python scripts) makes it highly compatible with other leading agentic software engineering assistants:

### 1. Gemini CLI (Native)
*   **Workflow:** Installs globally using `gemini skills install` and triggers automatically via session slash commands or natural language.
*   **Sample Prompt:** *"sync AI Guard domains"*

### 2. Claude Code (Anthropic) / Cursor IDE
*   **Workflow:** These tools inherently read Markdown files within the workspace context. By cloning this repository into a `.claude/skills/` or general workspace directory, their AI models will parse the `SKILL.md` rules and autonomously execute the provided Python commands.
*   **Sample Prompt:** *"Please execute the AI Guard domain sync procedure detailed in the skill markdown file."*

### 3. GitHub Copilot Workspace
*   **Workflow:** Mention `@workspace` and direct it to the `SKILL.md` guidelines. Copilot will synthesize a plan and run the terminal commands to process the sync.

---

## Prerequisites

1. **Python 3.7+** (No external `pip` packages required).
2. **Zscaler ZIdentity (OneAPI) Credentials**: You need a Client ID and Secret that has read/write permissions to ZIA IP Destination Groups and the ability to activate configurations.

## Manual Execution (Without an AI Agent)

1. **Clone or Download** this directory.
2. **Configure your environment**:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and fill in your details:
   ```ini
   ZSCALER_CLIENT_ID="your_client_id"
   ZSCALER_CLIENT_SECRET="your_secret"
   ZSCALER_VANITY_DOMAIN="your_vanity_domain"
   ```
   *Note: Make sure to `export` these variables into your shell session before running, or use a tool like `dotenv` if executing via a runner.*

3. **Run the Script**:
   ```bash
   python3 sync_domains.py
   ```

---

## Scheduling as a Cron Job (Weekly Automation)

To ensure your firewall is continuously updated with the latest AI domains as soon as Zscaler publishes them, you can schedule this script to run silently on a server or workstation via `cron`.

### Step 1: Create a wrapper script (`run_sync.sh`)
Create a shell script that loads the environment variables and calls Python:
```bash
#!/bin/bash
# /path/to/zscaler-aiguard-domain-sync/run_sync.sh

export ZSCALER_CLIENT_ID="your_client_id"
export ZSCALER_CLIENT_SECRET="your_secret"
export ZSCALER_VANITY_DOMAIN="your_vanity_domain"

# Execute the python script
/usr/bin/python3 /path/to/zscaler-aiguard-domain-sync/sync_domains.py
```
Make it executable: `chmod +x run_sync.sh`

### Step 2: Add it to Crontab
Open your crontab editor:
```bash
crontab -e
```
Add the following line to run the synchronization every Sunday at 2:00 AM, appending the output to a log file:
```cron
0 2 * * 0 /path/to/zscaler-aiguard-domain-sync/run_sync.sh >> /var/log/zscaler_aiguard_sync.log 2>&1
```
