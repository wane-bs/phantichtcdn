#!/usr/bin/env python3
"""
Lovable Fast Bulk Sync Tool
Đồng bộ toàn bộ file mã nguồn từ Lovable Project về local frontend/
Sử dụng access token từ ~/.mcp-auth/mcp-remote-v1/*.json
"""

import os
import sys
import json
import time
from pathlib import Path
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

PROJECT_ID = "752f2eb3-3d59-4847-b822-4ae9af248a85"
TARGET_DIR = Path(__file__).resolve().parent.parent / "frontend"
TOKEN_DIR = Path.home() / ".mcp-auth" / "mcp-remote-v1"

def get_access_token():
    token_files = list(TOKEN_DIR.glob("*_tokens.json"))
    if not token_files:
        raise FileNotFoundError(f"Không tìm thấy token json nào trong {TOKEN_DIR}")
    token_file = max(token_files, key=lambda f: f.stat().st_mtime)
    with open(token_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["access_token"]

def call_lovable_tool(token, tool_name, arguments):
    payload = {
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000) % 1000000,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    
    resp = requests.post("https://mcp.lovable.dev/mcp", json=payload, headers=headers, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:300]}")
    
    # Parse SSE message
    lines = resp.text.split("\n")
    for line in lines:
        if line.startswith("data: "):
            msg = json.loads(line[6:])
            if "error" in msg:
                raise RuntimeError(f"RPC Error: {msg['error']}")
            return msg.get("result", {})
    return {}

def list_all_files(token, project_id):
    files = []
    cursor = None
    while True:
        args = {"project_id": project_id, "limit": 100}
        if cursor:
            args["cursor"] = cursor
        res = call_lovable_tool(token, "list_files", args)
        
        # Check structuredContent or parse content[0].text
        data_files = []
        pagination = {}
        if "structuredContent" in res and res["structuredContent"]:
            data_files = res["structuredContent"].get("data", [])
            pagination = res["structuredContent"].get("pagination", {})
        elif "content" in res and res["content"]:
            try:
                parsed = json.loads(res["content"][0].get("text", "{}"))
                data_files = parsed.get("data", [])
                pagination = parsed.get("pagination", {})
            except Exception:
                pass
                
        files.extend(data_files)
        if not pagination.get("has_more", False) or not pagination.get("next_cursor"):
            break
        cursor = pagination.get("next_cursor")
    return files

def download_and_save_file(token, project_id, file_info, target_dir):
    rel_path = file_info["path"]
    is_binary = file_info.get("binary", False)
    local_path = target_dir / rel_path
    local_path.parent.mkdir(parents=True, exist_ok=True)
    
    if is_binary:
        # Tải qua get_file_upload_url hoặc download endpoint nếu cần, tạm thời pass nếu không có
        # Đối với favicon.ico hoặc static media
        return rel_path, "SKIP_BINARY"
        
    res = call_lovable_tool(token, "read_file", {"project_id": project_id, "path": rel_path})
    content_list = res.get("content", [])
    if not content_list:
        return rel_path, "EMPTY"
    
    text_content = content_list[0].get("text", "")
    with open(local_path, "w", encoding="utf-8") as f:
        f.write(text_content)
    return rel_path, "OK"

def main():
    print(f"[*] Khởi động đồng bộ mã nguồn Lovable (Project ID: {PROJECT_ID})")
    token = get_access_token()
    print("[*] Đã xác thực token thành công.")
    
    files = list_all_files(token, PROJECT_ID)
    print(f"[*] Tìm thấy tổng cộng {len(files)} files trên Lovable.")
    
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[*] Đích đồng bộ: {TARGET_DIR}")
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    # Đồng bộ song song bằng ThreadPoolExecutor (10 luồng)
    with ThreadPoolExecutor(max_workers=8) as executor:
        future_to_file = {
            executor.submit(download_and_save_file, token, PROJECT_ID, f, TARGET_DIR): f["path"]
            for f in files
        }
        for future in as_completed(future_to_file):
            path = future_to_file[future]
            try:
                rel_path, status = future.result()
                if status == "OK":
                    print(f"  [+] Synced: {rel_path}")
                    success_count += 1
                elif status == "SKIP_BINARY":
                    print(f"  [-] Skipped binary: {rel_path}")
                    skip_count += 1
                else:
                    print(f"  [?] {rel_path}: {status}")
            except Exception as e:
                print(f"  [!] Lỗi khi tải {path}: {e}")
                error_count += 1

    print("\n" + "=" * 60)
    print(f"[✓] HOÀN TẤT ĐỒNG BỘ LOVABLE -> LOCAL:")
    print(f"    - Thành công: {success_count} files")
    print(f"    - Bỏ qua (binary): {skip_count} files")
    print(f"    - Lỗi: {error_count} files")
    print("=" * 60)

if __name__ == "__main__":
    main()
