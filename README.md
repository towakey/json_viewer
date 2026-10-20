# json_viewer

Web上でJSONファイルを閲覧・編集するツール。
Windows Server + IIS + Python CGI 環境で動作します（外部ライブラリ・CDN不要、Python標準モジュールのみ）。

## 機能

- **閲覧**: JSONをツリー形式で折りたたみ表示（既定で2階層まで展開）
- **編集（ツリー）**: 値・キー名の変更、型変換（string/number/boolean/null/object/array）、子要素の追加・削除
- **編集（テキスト）**: 生のJSONテキストを直接編集、整形（フォーマット）機能付き
- **JSONエラー検査**: テキスト編集中のリアルタイム検証、エラーの行・桁表示、クリックでエラー行へジャンプ。保存時にもサーバー側で再検証（エラーがあると保存しない）
- **検索**: キー名・値でのフィルタ（ヒット箇所をハイライト＆自動展開）
- **保存**: 保存前にタイムスタンプ付きバックアップを自動作成
- **ローカルファイル**: 「ファイルを開く」でサーバー上にないJSONファイルの閲覧・編集・ダウンロードも可能

## ファイル構成

| ファイル | 説明 |
|---|---|
| `index.html` | 画面（HTML+CSS+JS、単一ファイル） |
| `list_json.py` | JSONファイル一覧取得CGI |
| `load_json.py` | JSONファイル読み込みCGI |
| `save_json.py` | JSON検証・保存CGI |
| `common.py` | 共通モジュール（CGI応答・パス検証など） |
| `setting.json` | 設定ファイル |
| `web.config` | IIS設定 |
| `test_server.py` | ローカルテスト用CGIサーバー |
| `json_files/` | 編集対象のJSONファイル置き場 |
| `json_files/backup/` | 保存時バックアップの出力先 |

## 設定（setting.json）

```json
{
  "json_directory": "json_files",
  "read_encoding": "utf-8",
  "write_encoding": "utf-8",
  "create_backup": true,
  "backup_directory": "json_files/backup",
  "allowed_extensions": [".json"]
}
```

編集したいJSONファイルを `json_directory` に置くと一覧に表示されます。

## IISセットアップ

1. IISにCGI機能をインストール（役割サービス「CGI」）
2. サイト/アプリケーションに本フォルダを配置
3. `web.config` の `scriptProcessor` のPythonパスを環境に合わせて変更（既定: `C:\Python37\python.exe`）
4. `json_files` フォルダにIISワーカープロセスの書き込み権限を付与
5. `http://サーバー/フォルダ名/` にアクセス

## ローカルでの動作確認

```
python test_server.py
```

→ http://localhost:8080/ を開く（.py がCGIとして実行されます）
