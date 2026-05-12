#!/usr/bin/env python3
"""
Win側 Claude Desktop config の gemini キー更新スクリプト
実行: python update_gemini_key_win.py
完了後はこのファイルとBox上のオリジナルを削除してください
"""
import json
import os
import sys

config_path = os.path.expandvars(r'%APPDATA%\Claude\claude_desktop_config.json')

if not os.path.exists(config_path):
    print(f"ERROR: config not found at {config_path}")
    sys.exit(1)

with open(config_path, 'r', encoding='utf-8') as f:
    cfg = json.load(f)

new_key = "AIzaSyBNhGN43NS2dAuZ64_1qdm_9iSXLesS1ow"

servers = cfg.get('mcpServers', {})
if 'gemini' not in servers:
    print("ERROR: 'gemini' section not found in mcpServers")
    sys.exit(1)

old_key = servers['gemini'].get('env', {}).get('GEMINI_API_KEY', '')
servers['gemini'].setdefault('env', {})['GEMINI_API_KEY'] = new_key

with open(config_path, 'w', encoding='utf-8') as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)

print(f"OK: updated gemini key in {config_path}")
print(f"  old key tail: ...{old_key[-6:] if old_key else '(empty)'}")
print(f"  new key tail: ...{new_key[-6:]}")
print("Next: completely quit Claude Desktop (system tray) and restart it.")
