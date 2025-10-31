import re
import json
from google import genai
from google.genai import types
# from IPython.display import display, Markdown # .pyファイルからは削除

def generate_final_sitemap(client, identity):
    """
    法人格に基づき、Webサイトの階層的なサイトマップを生成させる。
    """
    if client is None:
        return "❌ Geminiクライアントが初期化されていません。"

    prompt = f"""
    あなたはウェブサイトのUXアーキテクトです。
    以下の「法人のアイデンティティ」に基づき、ユーザーの論理的思考を助ける**階層的なサイトマップ**をMarkdown形式で生成してください。

    ### サイトマップ生成のルール
    1. サイトの核となるメッセージと構造を反映すること。
    2. グローバルナビゲーションは、**VISION, SOLUTIONS, INSIGHTS, COLLABORATION, CONTACT**の5つをレベル1の項目とすること。
    3. 法人のミッション（データサイエンスPDCA、個別最適化）を反映した具体的なレベル2のページ構造を設計すること。
    4. 見出しは「## サイトマップ: [サイト名]」から開始してください。

    ### 法人アイデンティティ
    {identity}
    """

    print("Geminiモデルで最終サイトマップの階層構造を生成しています...")
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        return f"❌ サイトマップの生成中にエラーが発生しました: {e}"

def generate_content_strategy(client, identity, sitemap):
    """
    法人格とサイトマップに基づき、トップページと主要ページのコンテンツ戦略の骨子を生成させる。
    """
    if client is None:
        return "❌ Geminiクライアントが初期化されていません。"

    prompt = f"""
    あなたはデータサイエンス企業のコンテンツストラテジストです。
    以下の「法人のアイデンティティ」と「サイトマップ」に基づき、トップページと主要ページのコンテンツ戦略（骨子）を策定してください。

    ### 策定ルール
    1. **ターゲット:** Society 5.0の変革に関心のあるビジネスリーダー、研究者、および未来志向の生活者。
    2. **トーン:** 先進的、分析的、論理的、信頼感を重視すること。
    3. **出力フォーマット:** 3つのセクションに分けて、具体的な見出し案と概要を箇条書きで記述すること。

    ### 法人アイデンティティ
    {identity}

    ### 確定済みサイトマップの主要構造
    {sitemap}

    ### コンテンツ戦略の策定（出力）

    --- A. トップページ (Homepage) 戦略 ---
    - ヒーローセクション（ファーストビュー）のコピー案（最も重要なメッセージ）:
    - 主要なナビゲーションセクションと、トップページに配置すべきコンテンツの概要:
    - CTA（コールトゥアクション）の配置戦略:

    --- B. VISION ページ戦略 (信頼性の確立) ---
    - ページ全体の目的: 貴社の哲学と主張の「科学的根拠」を示すこと。
    - 最重要コンテンツ「Webデータ分析の科学的根拠」に配置すべき見出しと論理構成:

    --- C. SOLUTIONS ページ戦略 (実行力の証明) ---
    - ページ全体の目的: 抽象的な「個別最適化」を具体的な「PDCAメソッド」と「事例」で裏付けること。
    - 「個別最適化メソッド: データサイエンスPDCAサイクル」の詳細な構成案:
    - 「導入事例」で強調すべき成功のポイント:
    """

    print("Geminiモデルでコンテンツ戦略を策定しています...")
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        return f"❌ コンテンツ戦略の生成中にエラーが発生しました: {e}"

def generate_target_page_list(client, identity, strategy):
    """
    法人格と戦略に基づき、ナビゲーションに必要な全ページのリストをJSON形式で生成する。
    (サブディレクトリ構造を反映するバージョン)
    """
    prompt_extract = f"""
    あなたは、Webサイトのアーキテクトです。以下の「法人格」と「コンテンツ戦略」に基づき、サイトのグローバルナビゲーションを構成する**全ての固定ページ（全10ページ程度）**のリストを、以下のJSONリスト形式で生成してください。

    ### 重要なルール
    1. グローバルナビゲーションの全要素（VISION, SOLUTIONS, INSIGHTS, COLLABORATION, CONTACT）を含めること。
    2. **ファイル構造:** 主要セクションは、**サブディレクトリに配置**し、ファイル名を **`セクション名/index.html`** としてください。（例: vision/index.html）
    3. ユーティリティページ（ポリシー）は、`legal/` ディレクトリに配置してください。（例: legal/privacy-policy.html）
    4. 目的 (purpose) は、そのページが持つべき戦略的な役割を簡潔に記述すること。

    【抽出フォーマット】
    [
      {{"title": "ホーム", "file_name": "index.html", "purpose": "サイトの顔。ヒーローセクションと、VISION、SOLUTIONSなど各セクションへの簡潔な概要と強いCTAを配置する。"}},
      {{"title": "理念・哲学", "file_name": "vision/index.html", "purpose": "当社のパーパス、ミッション、ビジョン、そして「Webデータ分析の科学的根拠」を論理的・実証的に提示し、企業の哲学と主張への信頼と共感を醸成する。"}},
      ... (全ページを完成させる)
    ]

    ### 法人のアイデンティティ
    {identity}

    ### コンテンツ戦略の要点
    {strategy}
    """

    print("\n📢 AIが戦略に基づき、ターゲットページリストを動的生成中...")
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt_extract,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        target_list = json.loads(response.text.strip())
        print(f"✅ ターゲットリストの抽出と構造化に成功しました ({len(target_list)} 件)。")
        return target_list
    except Exception as e:
        print(f"❌ ターゲットリストの動的抽出に失敗しました: {e}")
        return []
