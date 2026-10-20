#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""共通ユーティリティ（CGI応答・設定読み込み・パス検証）"""

import csv
import hmac
import json
import os
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SETTING_PATH = os.path.join(SCRIPT_DIR, "setting.json")
HISTORY_PATH = os.path.join(SCRIPT_DIR, "history.csv")


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


def check_password(setting, password):
    """save_password 未設定なら常にOK。設定済みなら一致を確認。"""
    expected = setting.get("save_password", "")
    if not expected:
        return True
    if password is None:
        password = ""
    return hmac.compare_digest(
        expected.encode("utf-8"), password.encode("utf-8")
    )


def _value_summary(v, limit=80):
    """履歴用に値を短い文字列化"""
    if isinstance(v, dict):
        return "object({}件)".format(len(v))
    if isinstance(v, list):
        return "array({}件)".format(len(v))
    s = json.dumps(v, ensure_ascii=False)
    if len(s) > limit:
        s = s[:limit] + "…"
    return s


def json_diff(old, new, path="", max_items=200):
    """2つのJSON値の差分を [{type,path,before,after}] で返す"""
    changes = []

    def add(kind, p, before, after):
        if len(changes) < max_items:
            changes.append({
                "type": kind,
                "path": p or "(root)",
                "before": _value_summary(before) if before is not _MISSING else "",
                "after": _value_summary(after) if after is not _MISSING else "",
            })

    def child(p, key):
        return p + "." + str(key) if p else str(key)

    def walk(o, n, p):
        if isinstance(o, dict) and isinstance(n, dict):
            for k in o:
                if k not in n:
                    add("削除", child(p, k), o[k], _MISSING)
                else:
                    walk(o[k], n[k], child(p, k))
            for k in n:
                if k not in o:
                    add("追加", child(p, k), _MISSING, n[k])
        elif isinstance(o, list) and isinstance(n, list):
            for i in range(min(len(o), len(n))):
                walk(o[i], n[i], child(p, i))
            for i in range(min(len(o), len(n)), len(o)):
                add("削除", child(p, i), o[i], _MISSING)
            for i in range(min(len(o), len(n)), len(n)):
                add("追加", child(p, i), _MISSING, n[i])
        elif o != n:
            add("変更", p, o, n)

    walk(old, new, path)
    return changes


class _Missing(object):
    pass


_MISSING = _Missing()


def write_history(filename, action, detail=""):
    """history.csv に履歴を追記（UTF-8 BOM付き、Excel互換）"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_exists = os.path.exists(HISTORY_PATH)
    try:
        with open(HISTORY_PATH, mode="a", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f, lineterminator="\r\n")
            if not file_exists:
                writer.writerow(["日時", "ファイル", "操作", "詳細"])
            writer.writerow([timestamp, filename, action, detail])
    except Exception:
        pass
