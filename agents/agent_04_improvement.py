import os
import re
import json
import pandas as pd
from bs4 import BeautifulSoup
from google import genai
from google.genai import types

# (analyze_article_structure, generate_article_purpose は変更なし)
def analyze_article_structure(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            soup = BeautifulSoup(content, 'html.parser')
        page_title = soup.find('title').get_text() if soup.find('title') else os.path.basename(file_path)
        main_content_area = soup.find('main')
        temp_soup = BeautifulSoup(content, 'html.parser')
        for tag in temp_soup.find_all(["script", "style", "nav", "header", "footer"]):
            tag.decompose()
        headings = []
        if main_content_area:
            for tag in main_content_area.find_all(['h1', 'h2', 'h3']):
                headings.append(f"<{tag.name}> {tag.get_text().strip()}")
        clean_text = temp_soup.get_text(separator='\n', strip=True)
        return {
            "page_title": page_title.split('|')[0].strip(),
            "structure": "\n".join(headings),
            "full_text_excerpt": clean_text[:500].replace('\n', ' ').strip() + "..."
        }, None
    except Exception as e:
        return None, f"❌ 解析エラー: {e}"

def generate_article_purpose(client, article_data, identity):
    if client is None: return "❌ クライアント未設定"
    prompt = f"""
    あなたは、Webサイトのコンテンツ戦略家です。
    以下の「法人の哲学」と「記事の現在の構造・内容」を分析し、**サイト全体の戦略に照らして、この記事が持つべき戦略的目的 (Purpose)** を1文で生成してください。
    【重要】回答は生成された「Purpose」の**文字列のみ**を返してください。
    ### 法人の哲学 (CORPORATE IDENTITY)
    {identity}
    ### 対象記事の現状分析
    - 記事タイトル: {article_data['page_title']}
    - 見出し構造: {article_data['structure']}
    - 本文抜粋: {article_data['full_text_excerpt']}
    生成するPurpose (1文):
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        return f"❌ AI生成失敗: {e}"

def select_priority_section_by_data(client, df_all_data, identity, target_pages_list):
    if client is None:
        return {'file_name': 'vision/index.html', 'reason': 'クライアント未設定のため、戦略的基盤であるVISIONをフォールバックしました。'}
    data_markdown = df_all_data.to_markdown()

    df_target_pages_data = []
    for p in target_pages_list:
        df_target_pages_data.append({
            "file_name": p.get('file_name'),
            "title": p.get('title'),
            "summary": p.get('generated_purpose', p.get('summary', ''))
        })
    df_target_pages = pd.DataFrame(df_target_pages_data)

    prompt = f"""
    あなたはデータ駆動型のコンテンツ戦略責任者です。以下の情報を分析し、**サイト全体の戦略的バランスと信頼性の最大化**の観点から、次にリソースを投入すべきセクションを1つだけ選定してください。

    ### 貴社の目標と戦略的重み
    1. **戦略的貢献度の評価:** 各ページが、貴社の**パーパス（法人格）**達成にどの程度重要か評価してください。
    2. **欠損領域の特定:** パフォーマンスデータが均一なため、現在の**コンテンツの目的（summary）**が、その戦略的貢献度に見合うだけの深さや専門性を欠いているセクション（**論理的な欠損**）を特定してください。

    ### 🚨 最重要ルール：選定対象の限定 🚨
    - 選定する「file_name」は、**必ず各セクションのハブページ（`index.html`で終わるファイル）**の中から選んでください。
    - ユーティリティページ（legal/ や contact/）は優先度を極端に低くしてください。
    - **詳細記事（例: ...-7.html や article-1.html）を選んではいけません。** コアな戦略領域の `index.html` の中から選んでください。

    ### 法人格
    {identity}
    ### 分析対象ページリスト (ファイル名と目的)
    {df_target_pages.to_markdown(index=False)}
    ### パフォーマンスデータ (データが均一なため、戦略的論理を優先)
    {data_markdown}
    ---
    回答は以下のJSON形式のみで出力し、理由には**「なぜそのセクションがサイトの信頼性と説得力の向上に最も貢献するか」**を記述してください。
    {{"file_name": "[選定したファイル名]", "reason": "[選定した論理的根拠を記述]"}}
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        parsed_json = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
        if any(p.get('file_name') == parsed_json.get('file_name') for p in target_pages_list):
            return parsed_json
        else:
            return {'file_name': 'vision/index.html', 'reason': 'AIの選定結果が不適切なため、戦略的基盤であるVISIONをフォールバックしました。'}
    except Exception as e:
        print(f"❌ AI選定エラー: {e}")
        return {'file_name': 'vision/index.html', 'reason': 'API接続エラーまたはJSONパース失敗のため、戦略的基盤であるVISIONをフォールバックします。'}

# ⬇️ ここが修正された関数です
def generate_priority_article_titles(client, section_info, identity, count, start_number):
    """
    最優先セクションの目的を満たす、具体的な記事タイトル、要約、スラッグを企画する。
    """
    if client is None: return "❌ Geminiクライアントが初期化されていません。", []

    # [修正] 'generated_purpose' と 'summary' の両方に対応
    section_purpose = section_info.get('generated_purpose', section_info.get('summary', ''))

    prompt = f"""
    あなたは、SEOとデータサイエンスの専門家です。
    以下の「法人のアイデンティティ」と「最優先セクションの戦略的目的」に基づき、その目的に最も貢献する**具体的かつ専門性の高い記事タイトル、要約、SEOスラッグ（ファイル名）**を {count} 件生成してください。

    ### CRITICAL要件
    1. **スラッグの形式:** 英語小文字、ハイフン区切り、`.html` 拡張子で、**記事の内容を正確に反映**してください。
    2. **連番の開始点:** 生成する {count} 件の連番は、**既存のコンテンツを考慮し {start_number} から開始**してください。（例: ...-{start_number}.html, ...-{start_number + 1}.html, ...）
    3. **JSON出力:** 回答はJSON配列形式のみで出力してください。スラッグにはこの連番を含めてください。

    ### 最優先セクションの戦略的目的
    {section_info['title']} ({section_info['file_name']})
    目的: {section_purpose}

    ### 法人格
    {identity}
    ---
    回答は、以下のJSON配列形式のみで出力してください。
    [
      {{"title": "記事タイトル", "summary": "要約", "file_name": "seo-optimized-slug-{start_number}.html"}},
      ... ({count}件分)
    ]
    """

    print(f"📢 AIに {section_info['title']} セクション用の記事 {count} 件の企画を依頼中...")
    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        parsed_list = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
        print("✅ 記事企画の生成に成功しました。")
        return "", parsed_list
    except Exception as e:
        print(f"❌ APIまたはJSONパースエラー: {e}")
        return str(e), []
