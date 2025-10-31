import re
import os
import json
from google import genai
from google.genai import types

def generate_single_page_html(client, target_page, identity, strategy_full, page_list, retry_attempts=3):
    """
    ターゲットページ情報に基づいてプロンプトを動的に生成し、HTMLファイルを出力する。
    """
    if client is None:
        return "❌ Geminiクライアントが利用できません。"

    nav_structure = "\n".join([f' - {p["title"]} ({p["file_name"]})' for p in page_list])

    target_title = target_page['title']
    target_filename = target_page['file_name']
    target_purpose = target_page['purpose']

    if target_filename == 'index.html':
        content_instruction = f"トップページは、**詳細な説明は避け**、VISION、SOLUTIONS、INSIGHTSの各セクションを**簡潔なサマリー**と**詳細ページへの強いCTA**として表現してください。"
        content_focus = strategy_full
    else:
        content_instruction = f"ページの目的（{target_purpose}）を達成するため、**深い論理構成と具体的なデータサイエンスの記述**に焦点を当ててください。コンテンツは必ず**Tailwindクラス**を使用して、セクション単位で論理的に分離してください。"
        content_focus = f"**このページの具体的な目的と、必要なコンテンツの詳細:** {target_purpose}\n\n--- 全体戦略の要約 ---\n{strategy_full}"

    prompt_template = f"""
    あなたはワールドクラスのウェブデザイナーであり、フロントエンドエンジニアです。
    以下の「法人格/トーン」と「コンテンツ戦略」に基づき、**{target_title} ({target_filename}) 用の単一のモダンでレスポンシブなHTMLファイル**を生成してください。

    ### CRITICAL INSTRUCTION: 出力形式の厳守
    - **[START HTML CODE]** というマーカーからコードの記述を開始してください。
    - **必ず** `<!DOCTYPE html>` から `</html>` まで、全てのHTML構造を完全に記述してください。
    - **必ず** `\n```eof` で出力を完全に終了してください。（コードブロックは```htmlで開始してください）

    ### 必須要件 (CRITICAL REQUIREMENTS)
    1.  **デザインフレームの維持:** トップページのデザイン（配色、フォント、CSS変数、フッターの4カラム構造）を完全に維持してください。
    2.  **ナビゲーションの統合:** ヘッダーとフッターのリンクには、**ファイル名（例: vision/index.html, legal/privacy-policy.html）を正確に**使用してください。
    3.  **コンテンツの役割:** {content_instruction}
    4.  **Tailwind CSS:** CDNをロードし、全てのスタイリングにTailwindクラスを使用してください。

    ### ページ固有の入力データ
    - ページのタイトル: {target_title}
    - ページのファイル名: {target_filename}
    - ページの目的: {target_purpose}

    ### 全体的な入力データ
    - 法人格フレームワーク: {identity}
    - コンテンツ戦略（コンテンツ焦点）：{content_focus}
    - 確定した全ページリスト（ナビゲーション構造）:{nav_structure}

    [START HTML CODE]
    """

    for attempt in range(retry_attempts):
        print(f"  > HTMLコードの生成を開始中... (試行 {attempt + 1}/{retry_attempts}) for {target_filename}")
        try:
            response = client.models.generate_content(
                model="gemini-2.5-pro", # Proモデルを使用
                contents=prompt_template
            )
            raw_output = response.text.strip()

            # 終了マーカーを厳密にチェック
            if raw_output.endswith("</html>\n```eof"):
                match = re.search(r"```html\s*(.*?)\s*```eof", raw_output, re.DOTALL)
                if match:
                    return match.group(1).strip()

            print(f"警告: コードが途中で切れたか、終了マーカーが見つかりませんでした。 for {target_filename}")

        except Exception as e:
            print(f"エラーが発生しました: {e} for {target_filename}")

    return "❌ HTMLコードの生成に失敗しました。"
