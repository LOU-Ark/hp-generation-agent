import re
import os
import json
from google import genai
from google.genai import types

# ⬇️ [修正] GTM_ID と ADSENSE_CLIENT_ID を受け取る
def generate_single_page_html(client, target_page, identity, strategy_full, page_list, GTM_ID=None, ADSENSE_CLIENT_ID=None, retry_attempts=3):
    """
    ターゲットページ情報に基づいてプロンプトを動的に生成し、HTMLファイルを出力する。
    GTMとAdSenseのスニペットを自動で挿入する。
    """
    if client is None:
        return "❌ Geminiクライアントが利用できません。"

    nav_structure = "\n".join([f' - {p.get("title", "N/A")} ({p.get("file_name", "N/A")})' for p in page_list])

    target_title = target_page['title']
    target_filename = target_page['file_name']
    target_purpose = target_page['purpose']
    
    # --- GTMスニペットの挿入指示 ---
    gtm_instructions = ""
    if GTM_ID:
        print(f"  > GTM ID ({GTM_ID}) をHTMLに挿入します。")
        gtm_instructions = f"""
    5.  **GTM (Google Tag Manager) の挿入:**
        - <head> タグのできるだけ高い位置に以下のコードを挿入してください:
        <script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':
        new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],
        j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
        'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
        }})(window,document,'script','dataLayer','{GTM_ID}');</script>
        - <body> タグの直後に以下のコードを挿入してください:
        <noscript><iframe src="https://www.googletagmanager.com/ns.html?id={GTM_ID}"
        height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
        """
    else:
         print(f"  > GTM ID が指定されていないため、GTMタグは挿入しません。")
         
    # --- ⬇️ [追加] AdSenseスニペットの挿入指示 ---
    adsense_instructions = ""
    if ADSENSE_CLIENT_ID:
        print(f"  > AdSense Client ID ({ADSENSE_CLIENT_ID}) をHTMLに挿入します。")
        adsense_instructions = f"""
    6.  **Google AdSense の挿入:**
        - <head> タグ内に以下のコードを挿入してください:
        <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADSENSE_CLIENT_ID}"
             crossorigin="anonymous"></script>
        """
    else:
        print(f"  > AdSense ID が指定されていないため、AdSenseタグは挿入しません。")
    # --- ⬆️ [追加] ここまで ---

    if target_filename == 'index.html' or 'index.html' in target_filename:
        content_instruction = f"このページはハブページ（目次）です。目的（{target_purpose}）を達成するため、**深い論理構成と具体的な記述**に焦点を当ててください。"
    else:
        content_instruction = f"このページは詳細記事です。目的（{target_purpose}）を達成するため、**深い論理構成と具体的なデータサイエンスの記述**に焦点を当ててください。"
    
    content_focus = f"**このページの具体的な目的と、必要なコンテンツの詳細:** {target_purpose}\n"
    if strategy_full:
        content_focus += f"\n--- 全体戦略の要約 ---\n{strategy_full}"


    prompt_template = f"""
    あなたはワールドクラスのウェブデザイナーであり、フロントエンドエンジニアです。
    以下の「法人格/トーン」と「コンテンツ戦略」に基づき、**{target_title} ({target_filename}) 用の単一のモダンでレスポンシブなHTMLファイル**を生成してください。

    ### CRITICAL INSTRUCTION: 出力形式の厳守
    - **[START HTML CODE]** というマーカーからコードの記述を開始してください。
    - **必ず** `<!DOCTYPE html>` から `</html>` まで、全てのHTML構造を完全に記述してください。
    - **必ず** `\n```eof` で出力を完全に終了してください。（コードブロックは```htmlで開始してください）

    ### 必須要件 (CRITICAL REQUIREMENTS)
    1.  **デザインフレームの維持:** デザイン（配色、フォント、Tailwind CSS）を完全に維持してください。
    2.  **ナビゲーションの統合:** ヘッダーとフッターのリンクには、**ファイル名（例: vision/index.html）を正確に**使用してください。
    3.  **コンテンツの役割:** {content_instruction}
    4.  **Tailwind CSS:** CDNをロードし、全てのスタイリングにTailwindクラスを使用してください。
    {gtm_instructions}
    {adsense_instructions} 

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
                model="gemini-2.5-pro",
                contents=prompt_template
            )
            raw_output = response.text.strip()

            if raw_output.endswith("</html>\n```eof"):
                match = re.search(r"```html\s*(.*?)\s*```eof", raw_output, re.DOTALL)
                if match:
                    return match.group(1).strip()

            print(f"警告: コードが途中で切れたか、終了マーカーが見つかりませんでした。 for {target_filename}")

        except Exception as e:
            print(f"エラーが発生しました: {e} for {target_filename}")

    return "❌ HTMLコードの生成に失敗しました。"
