#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
save_json.py - JSON保存 / 検証CGI
POST: {"file": "name.json", "content": "<JSONテキスト>", "check_only": false}
- check_only=false: JSON検証 → バックアップ作成 → ファイル書き込み
- check_only=true : JSON検証のみ実行（検証結果だけ返す）
"""

import json
import os
import sys
from common import (
    send_json, load_setting, resolve_json_path, json_error_dict, make_backup,
)


def main():
    method = os.environ.get("REQUEST_METHOD", "GET").upper()
    if method == "OPTIONS":
        send_json({"success": True})
        return
    if method != "POST":
        send_json({"success": False, "error": "POST のみ受け付けます"})
        return

    try:
        setting = load_setting()
    except Exception as e:
        send_json({"success": False, "error": "setting.json 読み込み失敗: " + str(e)})
        return

    try:
        content_length = int(os.environ.get("CONTENT_LENGTH", 0))
        if content_length <= 0:
            send_json({"success": False, "error": "データが空です"})
            return
        raw = sys.stdin.buffer.read(content_length)
        data = json.loads(raw.decode("utf-8"))
    except Exception as e:
        send_json({"success": False, "error": "リクエスト解析失敗: " + str(e)})
        return

    filename = data.get("file", "")
    content = data.get("content", "")
    check_only = bool(data.get("check_only", False))

    path = resolve_json_path(setting, filename)
    if path is None:
        send_json({"success": False, "error": "不正なファイル名です: " + filename})
        return
    if not os.path.exists(path) and not check_only:
        send_json({"success": False, "error": "ファイルが見つかりません: " + filename})
        return

    # JSON検証
    try:
        json.loads(content)
    except json.JSONDecodeError as e:
        send_json(json_error_dict(e))
        return
    except Exception as e:
        send_json({"success": False, "error": "検証エラー: " + str(e)})
        return

    if check_only:
        send_json({"success": True, "valid": True, "message": "JSONは正常です"})
        return

    # バックアップ → 書き込み
    try:
        backup_path = make_backup(setting, path)
    except Exception as e:
        send_json({"success": False, "error": "バックアップ作成失敗: " + str(e)})
        return

    encoding = setting.get("write_encoding", "utf-8")
    try:
        with open(path, mode="w", encoding=encoding, newline="") as f:
            f.write(content)
    except Exception as e:
        send_json({"success": False, "error": "書き込みエラー: " + str(e)})
        return

    send_json({
        "success": True,
        "message": "保存しました",
        "file": filename,
        "backup": os.path.basename(backup_path) if backup_path else None,
    })


if __name__ == "__main__":
    main()
