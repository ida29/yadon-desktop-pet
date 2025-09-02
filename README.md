# ヤドンデスクトップペット 🦦

tmux のセッションとペインの状態を監視し、吹き出しでお知らせするヤドン（Slowpoke）のデスクトップペットアプリケーションです。tmux にゴリゴリ依存しています。

## 機能

- **ピクセルアートのヤドン**: 16x16ピクセルアートで顔がアニメーション
- **tmux連携**: tmux のセッションを監視し、セッション名を表示
- **アクティビティ監視**: CLI 出力の停止を検知して青い吹き出しでお知らせ
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

## 監視の仕組み（tmux）

- セッション数に応じてヤドンを出現（右下に整列）
- 各セッションのアクティブな「ウィンドウ/ペイン」を 1秒ごとに表示（`#S #I #P`）
- 対象CLI（例: claude/codex/gemini）の出力が止まったら、10秒でやわらかく通知、3分で「やるきスイッチ」（ON時）

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
 
