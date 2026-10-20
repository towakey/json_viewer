#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
load_json.py - JSONファイル読み込みCGI
GET ?file=name.json → {"success": true, "file": ..., "content": <生テキスト>,
                        "valid": true/false, "error_detail": {...}}
"""

import json
import os
import sys
from common import (
    send_json, load_setting, resolve_json_path, json_error_dict,
)

if sys.version_info[0] >= 3:
    from urllib.parse import parse_qs
else:
    from urlparse import parse_qs


def main():
    try:
        setting = load_setting()
    except Exception as e:
        send_json({"success": False, "error": "setting.json 読み込み失敗: " + str(e)})
        return

    parsed = parse_qs(os.environ.get("QUERY_STRING", ""), keep_blank_values=True)
    filename = parsed.get("file", [""])[0]

    path = resolve_json_path(setting, filename)
    if path is None:
        send_json({"success": False, "error": "不正なファイル名です: " + filename})
        return
    if not os.path.exists(path):
        send_json({"success": False, "error": "ファイルが見つかりません: " + filename})
        return

    encoding = setting.get("read_encoding", "utf-8")
    try:
        with open(path, mode="r", encoding=encoding) as f:
            content = f.read()
    except UnicodeDecodeError as e:
        send_json({
            "success": False,
            "error": "文字コードエラー({}): {}".format(encoding, e),
        })
        return
    except Exception as e:
        send_json({"success": False, "error": "読み込みエラー: " + str(e)})
        return

    resp = {
        "success": True,
        "file": filename,
        "content": content,
        "size": os.path.getsize(path),
        "mtime": os.path.getmtime(path),
        "valid": True,
    }
    try:
        json.loads(content)
    except json.JSONDecodeError as e:
        resp["valid"] = False
        resp["error_detail"] = json_error_dict(e)["error_detail"]

    send_json(resp)


if __name__ == "__main__":
    main()
