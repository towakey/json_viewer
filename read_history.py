#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
read_history.py - 変更履歴取得CGI
GET ?file=name.json（任意）→ {"success": true, "rows": [[日時,ファイル,操作,詳細],...]}
新しい順で返す。file 指定時はそのファイルのみ。
"""

import csv
import os
import sys
from common import send_json, load_setting, HISTORY_PATH

if sys.version_info[0] >= 3:
    from urllib.parse import parse_qs
else:
    from urlparse import parse_qs


def main():
    try:
        load_setting()  # 設定ファイルの存在確認のみ
    except Exception as e:
        send_json({"success": False, "error": "setting.json 読み込み失敗: " + str(e)})
        return

    parsed = parse_qs(os.environ.get("QUERY_STRING", ""), keep_blank_values=True)
    filename = parsed.get("file", [""])[0]

    rows = []
    if os.path.exists(HISTORY_PATH):
        try:
            with open(HISTORY_PATH, mode="r", encoding="utf-8-sig", newline="") as f:
                reader = csv.reader(f)
                for i, row in enumerate(reader):
                    if i == 0 or len(row) < 4:
                        continue
                    if filename and row[1] != filename:
                        continue
                    rows.append(row[:4])
        except Exception as e:
            send_json({"success": False, "error": "履歴読み込みエラー: " + str(e)})
            return

    rows.reverse()  # 新しい順
    send_json({"success": True, "rows": rows, "count": len(rows)})


if __name__ == "__main__":
    main()
