#!/bin/bash
# sprite_to_godot_v2.sh
# 使い方: ./sprite_to_godot_v2.sh "prompt" "Node/Path/Sprite2D"
#
# 例:
#   ./sprite_to_godot_v2.sh "red ant warrior" "Unit/Sprite2D"
#
# 必要な環境変数（~/.zshrcに設定済みのはず）:
#   export REPLICATE_API_TOKEN="r8_..."
#   export GITHUB_TOKEN="ghp_..."

set -e

PROMPT="${1:-pixel art game sprite}"
NODE_PATH="${2:-}"  # 省略可。指定するとGodotに自動割当

REPO="okdsgr/mvp-02"
BRANCH="main"
SPRITES_DIR="assets/sprites"
TIMESTAMP=$(date +%s)
FILENAME="sprite_${TIMESTAMP}.png"
GODOT_PATH="${SPRITES_DIR}/${FILENAME}"
RES_PATH="res://${GODOT_PATH}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GODOT_PROJECT_DIR="${HOME}/Dev/godot-projects/mvp-02"
SET_TEXTURE_SCRIPT="${SCRIPT_DIR}/godot_set_texture.py"

echo "🎨 生成中: ${PROMPT}"

# ── Step 1: Replicateで画像生成 ──────────────────────────────
REPLICATE_RESPONSE=$(curl -s -X POST \
  "https://api.replicate.com/v1/models/black-forest-labs/flux-schnell/predictions" \
  -H "Authorization: Bearer ${REPLICATE_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "Prefer: wait=60" \
  -d "{
    \"input\": {
      \"prompt\": \"${PROMPT}, pixel art style, game sprite, white background, clean edges\",
      \"num_outputs\": 1,
      \"output_format\": \"png\"
    }
  }")

IMAGE_URL=$(echo "$REPLICATE_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
output = data.get('output')
if output and isinstance(output, list) and len(output) > 0:
    print(output[0])
else:
    print('ERROR: ' + json.dumps(data))
    exit(1)
")

if [[ "$IMAGE_URL" == ERROR* ]]; then
  echo "❌ Replicate エラー: $IMAGE_URL"
  exit 1
fi

echo "✅ 画像生成完了: $IMAGE_URL"

# ── Step 2: 画像ダウンロード → base64 ────────────────────────
TMP_FILE="/tmp/${FILENAME}"
curl -s -o "$TMP_FILE" "$IMAGE_URL"
BASE64_CONTENT=$(base64 < "$TMP_FILE")
rm "$TMP_FILE"
echo "✅ ダウンロード完了"

# ── Step 3: GitHubにコミット ──────────────────────────────────
GITHUB_RESPONSE=$(curl -s -X PUT \
  "https://api.github.com/repos/${REPO}/contents/${GODOT_PATH}" \
  -H "Authorization: Bearer ${GITHUB_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"Add sprite: ${FILENAME} [auto]\",
    \"content\": \"${BASE64_CONTENT}\",
    \"branch\": \"${BRANCH}\"
  }")

COMMIT_URL=$(echo "$GITHUB_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
commit = data.get('commit', {})
url = commit.get('html_url', '')
if url:
    print(url)
else:
    print('ERROR: ' + json.dumps(data))
    exit(1)
")

if [[ "$COMMIT_URL" == ERROR* ]]; then
  echo "❌ GitHub エラー: $COMMIT_URL"
  exit 1
fi

echo "✅ GitHubコミット完了: $COMMIT_URL"

# ── Step 4: git pull ──────────────────────────────────────────
echo "📥 git pull中..."
cd "${GODOT_PROJECT_DIR}"
git pull
echo "✅ git pull完了: ${GODOT_PATH}"

# ── Step 5: Godotにテクスチャ割当（NODE_PATH指定時のみ） ──────
if [ -n "$NODE_PATH" ]; then
  if [ -f "$SET_TEXTURE_SCRIPT" ]; then
    echo "🎯 Godotにテクスチャを割当中: ${NODE_PATH}"
    python3 "$SET_TEXTURE_SCRIPT" "$NODE_PATH" "$RES_PATH"
  else
    echo "⚠️  godot_set_texture.py が見つかりません: ${SET_TEXTURE_SCRIPT}"
    echo "   手動で割当: ノード「${NODE_PATH}」のtextureに「${RES_PATH}」を設定してください"
  fi
else
  echo ""
  echo "💡 Godotノードに割当するには:"
  echo "   python3 ${SET_TEXTURE_SCRIPT} \"Node/Sprite2D\" \"${RES_PATH}\""
fi

echo ""
echo "📁 Godotパス: ${RES_PATH}"
