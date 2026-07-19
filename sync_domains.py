import urllib.request
import json
import ssl
import os
import re
import sys

# =====================================================================
# Configuration
# =====================================================================
# Load credentials from environment variables to ensure no hardcoded secrets.
CLIENT_ID = os.environ.get('ZSCALER_CLIENT_ID')
CLIENT_SECRET = os.environ.get('ZSCALER_CLIENT_SECRET')
VANITY_DOMAIN = os.environ.get('ZSCALER_VANITY_DOMAIN')

# Defaults
API_BASE = os.environ.get('ZSCALER_API_URL', 'api.zsapi.net')
TARGET_GROUP_NAME = os.environ.get('TARGET_GROUP_NAME', 'AI Guard Destinations')
GROUP_DESCRIPTION = "Auto-synced AI Guard Required Domains (Managed by API)"

def validate_environment():
    missing = []
    if not CLIENT_ID: missing.append('ZSCALER_CLIENT_ID')
    if not CLIENT_SECRET: missing.append('ZSCALER_CLIENT_SECRET')
    if not VANITY_DOMAIN: missing.append('ZSCALER_VANITY_DOMAIN')
    
    if missing:
        print(f"❌ ERROR: Missing required environment variables: {', '.join(missing)}")
        print("Please configure your .env file or export them before running.")
        sys.exit(1)

def get_zia_token():
    token_url = f'https://{VANITY_DOMAIN}.zslogin.net/oauth2/v1/token'
    payload = {
        'grant_type': 'client_credentials', 
        'client_id': CLIENT_ID, 
        'client_secret': CLIENT_SECRET, 
        'audience': 'https://api.zscaler.com'
    }
    
    import urllib.parse
    data = urllib.parse.urlencode(payload).encode()
    req = urllib.request.Request(token_url, data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    
    try:
        res = urllib.request.urlopen(req, context=ssl._create_unverified_context())
        return json.loads(res.read())['access_token']
    except urllib.error.HTTPError as e:
        print(f"❌ Failed to get ZIdentity token. HTTP {e.code}: {e.read().decode('utf-8', errors='ignore')}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to get ZIdentity token: {e}")
        sys.exit(1)

def extract_domains():
    help_url = "https://help.zscaler.com/zapi/fetch-data?url_alias=/secure-ai-users/integrating-zia-ai-guard&view_type=full&cloud=false&domain=zscaler&applicable_category=&applicable_version=&applicable_parent_version=&applicable_product=&keyword=&language=en&_format=json"
    req_help = urllib.request.Request(help_url)
    try:
        res_help = urllib.request.urlopen(req_help, context=ssl._create_unverified_context())
        help_data = json.loads(res_help.read())
        html_content = help_data['data']['body']['content']
    except Exception as e:
        print(f"❌ Failed to fetch Zscaler Help documentation: {e}")
        sys.exit(1)
    
    table_match = re.search(r'<table[^>]*>(.*?)</table>', html_content, re.IGNORECASE | re.DOTALL)
    if not table_match:
        raise Exception("Domains table not found in help content.")
        
    tbody_match = re.search(r'<tbody[^>]*>(.*?)</tbody>', table_match.group(1), re.IGNORECASE | re.DOTALL)
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', tbody_match.group(1), re.IGNORECASE | re.DOTALL)
    
    domains = set()
    for row in rows:
        cols = re.findall(r'<td[^>]*>(.*?)</td>', row, re.IGNORECASE | re.DOTALL)
        if len(cols) >= 3:
            cell_text = re.sub(r'<[^>]+>', ' ', cols[2])
            words = cell_text.split()
            for w in words:
                w = w.strip()
                # Check for standard FQDN format, avoiding pure instructional text
                if w and '.' in w and not any(x in w.lower() for x in ['enter', 'domain', 'region']):
                    w = w.rstrip(',:;')
                    domains.add(w)
                    
    processed_domains = []
    for d in domains:
        if d.startswith('.'):
            processed_domains.append('*' + d)
        else:
            processed_domains.append(d)
    
    return sorted(list(set(processed_domains)))

def main():
    print("🛡️  Starting Zscaler AI Guard Domain Sync...")
    validate_environment()
    
    print("🔑 Authenticating with ZIdentity...")
    token = get_zia_token()
    base_endpoint = f"https://{API_BASE}/zia/api/v1/ipDestinationGroups"
    
    print(f"📥 Fetching existing '{TARGET_GROUP_NAME}' group...")
    try:
        req_api = urllib.request.Request(base_endpoint, headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'})
        res = urllib.request.urlopen(req_api, context=ssl._create_unverified_context())
        groups = json.loads(res.read())
    except Exception as e:
        print(f"❌ Failed to fetch IP Destination Groups: {e}")
        sys.exit(1)
    
    target_group = next((g for g in groups if g['name'] == TARGET_GROUP_NAME), None)
    
    print("🌐 Scraping latest AI Guard domains from Zscaler Help Portal...")
    domains = extract_domains()
    print(f"✅ Extracted {len(domains)} supported domains.")
    
    if target_group:
        print(f"\n🔄 Group '{TARGET_GROUP_NAME}' exists (ID: {target_group['id']}). Updating...")
        target_group['addresses'] = domains
        target_group['ipAddresses'] = domains
        
        try:
            req_put = urllib.request.Request(f"{base_endpoint}/{target_group['id']}", data=json.dumps(target_group).encode(), headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}, method='PUT')
            urllib.request.urlopen(req_put, context=ssl._create_unverified_context())
            print("   ✅ Group successfully updated via API.")
        except Exception as e:
            print(f"   ❌ Failed to update group: {e}")
            sys.exit(1)
    else:
        print(f"\n➕ Group '{TARGET_GROUP_NAME}' does not exist. Creating...")
        payload = {
            "name": TARGET_GROUP_NAME,
            "type": "DSTN_DOMAIN",
            "addresses": domains,
            "ipAddresses": domains,
            "description": GROUP_DESCRIPTION
        }
        try:
            req_post = urllib.request.Request(base_endpoint, data=json.dumps(payload).encode(), headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}, method='POST')
            urllib.request.urlopen(req_post, context=ssl._create_unverified_context())
            print("   ✅ Group successfully created via API.")
        except Exception as e:
            print(f"   ❌ Failed to create group: {e}")
            sys.exit(1)
        
    print("\n🚀 Activating ZIA configuration...")
    try:
        act_url = f"https://{API_BASE}/zia/api/v1/status/activate"
        req_act = urllib.request.Request(act_url, data=b'{}', headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}, method='POST')
        urllib.request.urlopen(req_act, context=ssl._create_unverified_context())
        print("   ✅ Configuration activated.")
    except Exception as e:
        print(f"   ⚠️ Activation step failed or requires manual intervention: {e}")
        
    print("\n🔍 Verifying effective updates...")
    try:
        req_verify = urllib.request.Request(base_endpoint, headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'})
        res_verify = urllib.request.urlopen(req_verify, context=ssl._create_unverified_context())
        groups_verify = json.loads(res_verify.read())
        
        verified_group = next((g for g in groups_verify if g['name'] == TARGET_GROUP_NAME), None)
        if verified_group:
            print("✅ Verified Group state on API:")
            print(f"   Name: {verified_group['name']}")
            print(f"   Total Addresses Sync'd: {len(verified_group['addresses'])}")
        else:
            print("❌ Verification failed. Group not found.")
    except Exception as e:
        print(f"❌ Verification check failed: {e}")

if __name__ == '__main__':
    main()
