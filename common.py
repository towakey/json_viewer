#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""共通ユーティリティ（CGI応答・設定読み込み・パス検証）"""

import json
import os
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SETTING_PATH = os.path.join(SCRIPT_DIR, "setting.json")


def send_json(obj):
    body = (json.dumps(obj, ensure_ascii=False) + "\r\n").encode("utf-8")
    headers = (
        "Content-Type: application/json; charset=utf-8\r\n"
        "Access-Control-Allow-Origin: *\r\n"
        "Cache-Control: no-store\r\n"
        "Content-Length: {}\r\n"
        "\r\n"
    ).format(len(body)).encode("ascii")
    output = getattr(sys.stdout, "buffer", sys.stdout)
    output.write(headers + body)
    output.flush()


def load_setting():
    with open(SETTING_PATH, mode="r", encoding="utf-8") as f:
        return json.load(f)


def get_json_dir(setting):
    json_dir = setting.get("json_directory", "json_files")
    if not os.path.isabs(json_dir):
        json_dir = os.path.join(SCRIPT_DIR, json_dir)
    return json_dir


def get_allowed_extensions(setting):
    return [e.lower() for e in setting.get("allowed_extensions", [".json"])]


def resolve_json_path(setting, filename):
    """ファイル名を検証して json_directory 内の実パスを返す。不正なら None。"""
    if not filename:
        return None
    if os.path.basename(filename) != filename:
        return None  # パス区切り禁止（トラバーサル対策）
    _, ext = os.path.splitext(filename)
    if ext.lower() not in get_allowed_extensions(setting):
        return None
    json_dir = os.path.realpath(get_json_dir(setting))
    path = os.path.realpath(os.path.join(json_dir, filename))
    if not path.startswith(json_dir + os.sep):
        return None
    return path


def json_error_dict(e):
    """json.JSONDecodeError を API 応答用の dict に変換"""
    return {
        "success": False,
        "error": "JSONエラー: {} ({}行目 {}桁目)".format(e.msg, e.lineno, e.colno),
        "error_detail": {
            "message": e.msg,
            "line": e.lineno,
            "column": e.colno,
            "position": e.pos,
        },
    }


def make_backup(setting, path):
    if not setting.get("create_backup", True):
        return None
    backup_dir = setting.get("backup_directory", "backup")
    if not os.path.isabs(backup_dir):
        backup_dir = os.path.join(SCRIPT_DIR, backup_dir)
    if not os.path.isdir(backup_dir):
        os.makedirs(backup_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(
        backup_dir, os.path.basename(path) + "." + timestamp + ".bak"
    )
    import shutil
    shutil.copy2(path, backup_path)
    return backup_path
