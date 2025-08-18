# ヤドンデスクトップペット 🦦

Claude Codeのプロセスを監視し、フック機能と連携して吹き出しを表示するヤドン（Slowpoke）のデスクトップペットアプリケーションです。

## 機能

- **ピクセルアートのヤドン**: 16x16ピクセルアートで顔がアニメーション
- **Claude Code連携**: Claude Codeのプロセスを監視してPIDを表示
- **フック対応**: Claude Codeのフックに反応して吹き出しを表示
- **自動起動**: システム起動時に自動的に起動可能（macOS）
- **複数ヤドン対応**: 複数のClaude Codeプロセスに対して複数のヤドンを生成
- **スマート吹き出し**: ポケモンスタイルのテキストボックスが画面端で自動調整

## インストール

### 前提条件

```bash
# Python 3とPyQt6をインストール
pip install PyQt6
```

### クイックインストール（macOS）

```bash
# リポジトリをクローン
git clone https://github.com/ida29/yadon-desktop-pet-.git
cd yadon-desktop-pet-

# 自動起動用のインストールスクリプトを実行
./install.sh
```

### 手動実行

```bash
python3 yadon_pet.py
```

## Claude Codeフック統合

### Claude Codeでフックを設定

`~/.claude/settings.json`に以下を追加：

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/yadon-desktop-pet-/hook_notify.sh"
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/yadon-desktop-pet-/hook_stop.sh"
          }
        ]
      }
    ]
  }
}
```

**注意**: `/path/to/`をインストールディレクトリの実際のパスに置き換えてください。

### 利用可能なフック

- **Stopフック** (`hook_stop.sh`): Claude Codeが停止時に「ひとやすみするやぁん」を表示
- **Notificationフック** (`hook_notify.sh`): 通知時に「びびっときたやぁん」を表示

### カスタムフックメッセージ

フックファイルに書き込むことでヤドンにカスタムメッセージを送信できます：

```bash
# {PID}をClaude CodeのプロセスID（ヤドンの下に表示）に置き換え
echo "メッセージ" > /tmp/yadon_hook_{PID}.txt

# または汎用フックファイルを使用（最初のヤドンが応答）
echo "メッセージ" > /tmp/yadon_hook.txt
```

## 自動起動管理（macOS）

### 自動起動を有効化
```bash
./install.sh
```

### 自動起動を無効化
```bash
launchctl unload ~/Library/LaunchAgents/com.yadon.pet.plist
```

### 完全削除
```bash
launchctl unload ~/Library/LaunchAgents/com.yadon.pet.plist
rm ~/Library/LaunchAgents/com.yadon.pet.plist
```

## トラブルシューティング

## デバッグログ

- **メインログ**: `/tmp/yadon-pet.log`
- **エラーログ**: `/tmp/yadon-pet-error.log`
- **デバッグログ**: `/tmp/yadon_debug.log`
- **フックデバッグ**: `/tmp/hook_debug.log`

