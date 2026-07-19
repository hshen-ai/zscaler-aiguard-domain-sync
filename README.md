# Zscaler AI Guard Domain Sync

Zscaler AI Guard requires ZIA to intercept and forward specific Generative AI traffic to its inspection engines. This requires maintaining an up-to-date **IP Destination Group** containing all FQDNs for supported AI providers (like OpenAI, Anthropic, Google Gemini, etc.).

Because Zscaler continuously adds support for new AI applications, the required domains change over time. This tool actively scrapes the [Zscaler Help Portal](https://help.zscaler.com/secure-ai-users/integrating-zia-ai-guard), formats the newly discovered domains, and pushes them seamlessly to your live Zscaler ZIA tenant via the OneAPI.

## Features
- **Zero-Dependency Web Scraping:** Uses native Python libraries to extract the raw JSON backing the React.js Zscaler Help Portal, completely bypassing the need for a headless browser (like Selenium or Puppeteer).
- **Automated Formatting:** Pre-processes top-level domains (e.g., `.perplexity.ai` is automatically reformatted into a valid ZIA wildcard `*.perplexity.ai`).
- **Fully Idempotent:** If the target IP Destination Group doesn't exist, it creates it. If it does exist, it updates it via a complete override.
- **Auto-Activation:** Triggers a ZIA configuration activation command (`POST /status/activate`) instantly after applying changes.

---

## Prerequisites

1. **Python 3.7+** (No external `pip` packages required).
2. **Zscaler ZIdentity (OneAPI) Credentials**: You need a Client ID and Secret that has read/write permissions to ZIA IP Destination Groups and the ability to activate configurations.

## Quick Start (Manual Execution)

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
# /path/to/AIGuard-Domain-Sync/run_sync.sh

export ZSCALER_CLIENT_ID="your_client_id"
export ZSCALER_CLIENT_SECRET="your_secret"
export ZSCALER_VANITY_DOMAIN="your_vanity_domain"

# Execute the python script
/usr/bin/python3 /path/to/AIGuard-Domain-Sync/sync_domains.py
```
Make it executable: `chmod +x run_sync.sh`

### Step 2: Add it to Crontab
Open your crontab editor:
```bash
crontab -e
```
Add the following line to run the synchronization every Sunday at 2:00 AM, appending the output to a log file:
```cron
0 2 * * 0 /path/to/AIGuard-Domain-Sync/run_sync.sh >> /var/log/zscaler_aiguard_sync.log 2>&1
```

---

## Using as a Gemini CLI Skill

If you are using Google's **Gemini CLI** (or a compatible AI CLI agent), you can import this script as an autonomous "Skill".

A `SKILL.md` file is provided. Simply place the `SKILL.md` and `sync_domains.py` files into a dedicated skill folder in your Gemini environment (e.g., `~/.gemini/skills/aiguard-domain-sync/`).

Once loaded, you can simply type:
> *"sync AI Guard domains"*

Your AI agent will read the context instructions, automatically authenticate, execute the script, and report the results back to you in plain english!
