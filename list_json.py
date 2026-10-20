#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
list_json.py - JSONファイル一覧取得CGI
GET → {"success": true, "files": [{"name": ..., "size": ..., "mtime": ...}]}
"""

import os
from common import send_json, load_setting, get_json_dir, get_allowed_extensions


def main():
    try:
        setting = load_setting()
    except Exception as e:
        send_json({"success": False, "error": "setting.json 読み込み失敗: " + str(e)})
        return

    json_dir = get_json_dir(setting)
    if not os.path.isdir(json_dir):
        send_json({
            "success": False,
            "error": "JSONディレクトリが見つかりません: " + json_dir,
        })
        return

    exts = get_allowed_extensions(setting)
    files = []
    try:
        for name in sorted(os.listdir(json_dir)):
            path = os.path.join(json_dir, name)
            if not os.path.isfile(path):
                continue
            if os.path.splitext(name)[1].lower() not in exts:
                continue
            st = os.stat(path)
            files.append({
                "name": name,
                "size": st.st_size,
                "mtime": st.st_mtime,
            })
    except Exception as e:
        send_json({"success": False, "error": "一覧取得エラー: " + str(e)})
        return

    send_json({
        "success": True,
        "files": files,
        "password_required": bool(setting.get("save_password", "")),
    })


if __name__ == "__main__":
    main()
