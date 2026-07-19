# AI Guard Domain Sync Skill

## Context
Zscaler AI Guard acts as an inline proxy for Generative AI applications. To properly steer and inspect this traffic, ZIA requires an IP Destination Group configured with the FQDNs of all supported LLM providers. Zscaler regularly updates their help portal with new supported domains. This skill autonomously scrapes the official Zscaler help documentation, formats the required domains, and actively synchronizes them into the ZIA `AI Guard Destinations` IP Destination Group via the Zscaler OneAPI.

## Execution Rules
When the user asks you to "sync AI Guard domains", "update AI Guard destinations", or run the AI Guard domain sync, execute the following steps using the provided python script:

1. **Check/Create/Update Group:** Check if a group named "AI Guard Destinations" exists via the `https://api.zsapi.net/zia/api/v1/ipDestinationGroups` endpoint.
2. **Scrape Documentation:** Fetch `https://help.zscaler.com/secure-ai-users/integrating-zia-ai-guard` and extract all domains listed in the "Domains Required" column.
3. **Process Domains:** For any extracted domain that begins with a `.` (e.g., `.perplexity.ai`), prepend a `*` to make it a valid wildcard FQDN (e.g., `*.perplexity.ai`). Leave standard FQDNs untouched.
4. **Push Configuration:** Overwrite the existing `addresses` and `ipAddresses` in the group with the newly processed list, or create the group if it does not exist.
5. **Verify:** Perform a final GET request to verify the effective state of the updated group in the ZIA API.

## Execution Command
To perform this task, execute the bundled script:
python3 /Users/henryshen/.gemini/skills/aiguard-domain-sync/sync_domains.py
