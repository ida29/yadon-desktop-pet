# ヤドンデスクトップペット 🦦

tmux のセッションを監視し、tmux フックと連携して吹き出しを表示するヤドン（Slowpoke）のデスクトップペットアプリケーションです。tmux にゴリゴリ依存しています。

## 機能

- **ピクセルアートのヤドン**: 16x16ピクセルアートで顔がアニメーション
- **tmux連携**: tmux のセッションを監視し、セッション名を表示
- **フック対応**: tmux のフックに反応して吹き出しを表示
- **自動起動**: システム起動時に自動的に起動可能（macOS）
- **複数ヤドン対応**: 複数の tmux セッションに対して複数のヤドンを生成
- **スマート吹き出し**: ポケモンスタイルのテキストボックスが画面端で自動調整

## インストール

### 前提条件

```bash
# Python 3とPyQt6をインストール
pip install PyQt6
# tmux をインストール（Homebrew 例）
brew install tmux
```

### クイックインストール（macOS）

```bash
# リポジトリをクローン
git clone https://github.com/yida/yadon-desktop-pet.git
cd yadon-desktop-pet

# 自動起動用のインストールスクリプトを実行
./install.sh
```

### 手動実行

```bash
python3 yadon_pet.py
```

## tmux フック統合

### tmux でフックを設定

`.tmux.conf` に以下を追加してください（パスは環境に合わせて変更）：

```tmux
# セッション作成時に通知
set-hook -g session-created  "run-shell '/path/to/yadon-desktop-pet/hook_notify.sh #{session_name}'"

# セッション終了時に通知
set-hook -g session-closed   "run-shell '/path/to/yadon-desktop-pet/hook_stop.sh #{session_name}'"

# お好みで、ウィンドウ作成やフォーカス変更にも通知
# set-hook -g window-created   "run-shell '/path/to/yadon-desktop-pet/hook_notify.sh #{session_name}'"
# set-hook -g client-session-changed "run-shell '/path/to/yadon-desktop-pet/hook_notify.sh #{session_name}'"
```

`hook_notify.sh` / `hook_stop.sh` は引数のセッション名を使って `/tmp/tmux_hook_{session}.txt` にメッセージを書き込みます。

### 利用可能なフック

- **Stopフック** (`hook_stop.sh`): セッション終了時に「ひとやすみするやぁん」を表示
- **Notificationフック** (`hook_notify.sh`): 各種イベント時に「びびっときたやぁん」を表示

### カスタムフックメッセージ

フックファイルに書き込むことでヤドンにカスタムメッセージを送信できます：

```bash
# {SESSION} を対象 tmux セッション名（ヤドンの下に表示）に置き換え
echo "メッセージ" > /tmp/yadon_hook_{SESSION}.txt

# または汎用フックファイルを使用（最初のヤドンが応答）
echo "メッセージ" > /tmp/yadon_hook.txt
```

tmux 専用のフックファイルも利用できます：

```bash
echo "メッセージ" > /tmp/tmux_hook_{SESSION}.txt
echo "メッセージ" > /tmp/tmux_hook.txt
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
