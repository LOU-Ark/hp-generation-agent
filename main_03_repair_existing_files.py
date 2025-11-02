import os
import sys
import json
import shutil
from google import genai

# モジュールをインポート
from agents.agent_03_generation import generate_single_page_html 
from agents.agent_01_identity import generate_corporate_identity 
from agents.agent_04_improvement import select_priority_section_by_data
from utils.analysis_utils import create_placeholder_data
from utils.file_utils import load_markdown_table_to_list

# --- 0. 設定 ---
BASE_DIR = "docs" 
REPORTS_DIR = "output_reports"
PLAN_FILE = os.path.join(REPORTS_DIR, "planned_articles.md") 
STUB_FILE_SIZE_THRESHOLD = 1024 # (1KB) これ以下のファイルサイズを「スタブ」とみなす
DEFAULT_REPAIR_COUNT = 3 # ⬅️ 修復する件数

def setup_client():
    """Geminiクライアントを初期化"""
    try:
        from google.colab import userdata
        GOOGLE_API_KEY = userdata.get('GEMINI_API_KEY')
        if not GOOGLE_API_KEY:
            raise ValueError("GEMINI_API_KEY が Colab Secrets に設定されていません。")
        return genai.Client(api_key=GOOGLE_API_KEY)
    except ImportError:
        GOOGLE_API_KEY = os.environ.get('GEMINI_API_KEY')
        if not GOOGLE_API_KEY:
            raise EnvironmentError("GEMINI_API_KEY が環境変数に設定されていません。")
        return genai.Client(api_key=GOOGLE_API_KEY)
    except Exception as e:
        print(f"❌ クライアント初期化エラー: {e}")
        return None

def load_corporate_identity():
    """法人格をロードする。"""
    try:
        from agents.agent_01_identity import generate_corporate_identity
        with open("config/opinion.txt", 'r', encoding='utf-8') as f:
            RAW_VISION_INPUT = f.read()
        client = setup_client() 
        if client:
            return generate_corporate_identity(client, RAW_VISION_INPUT)
        else:
            raise Exception("クライアントの初期化に失敗")
    except Exception as e:
        print(f"警告: 法人格の動的ロードに失敗: {e}。ダミーを使用します。")
        return "パーパス: データによる個人の生活最適化。 トーン: 論理的、先進的。"

def main():
    print(f"--- 🛠️ HP 修復・再生成スクリプト (Top {DEFAULT_REPAIR_COUNT} スタブ記事のみ) 開始 ---")
    
    # --- 1. クライアント初期化と法人格の取得 ---
    gemini_client = setup_client()
    if gemini_client is None: sys.exit(1)
        
    CORPORATE_IDENTITY = load_corporate_identity()
    print("✅ 法人格をロードしました。")

    # --- 2. 計画(To-Be)の読み込み ---
    print(f"\n--- [ステップ1: 計画(To-Be)の読み込み] ---")
    if not os.path.exists(PLAN_FILE):
        print(f"❌ 計画ファイル ({PLAN_FILE}) が見つかりません。")
        sys.exit(1)
    all_planned_articles = load_markdown_table_to_list(PLAN_FILE) # ⬅️ 'generated_purpose' キーで読み込む
    if not all_planned_articles:
        print(f"❌ 計画ファイルの読み込みに失敗しました。")
        sys.exit(1)
    print(f"✅ 計画(To-Be): {len(all_planned_articles)} 件のタスクを読み込みました。")

    # --- 3. 修復対象（スタブ）の検出 ---
    print(f"\n--- [ステップ2: 修復対象（スタブ）の検出] ---")
    stub_articles = []
    
    if not os.path.isdir(BASE_DIR):
        print(f"❌ サイトディレクトリ ({BASE_DIR}) が見つかりません。")
        sys.exit(1)

    for plan in all_planned_articles:
        file_name = plan['file_name']
        full_path = os.path.join(BASE_DIR, file_name)

        if os.path.exists(full_path) and (not file_name.endswith('index.html')):
            try:
                if os.path.getsize(full_path) < STUB_FILE_SIZE_THRESHOLD:
                    stub_articles.append(plan)
            except OSError:
                continue 

    print(f"✅ 修復対象: {len(stub_articles)} 件の「スタブ記事」（1KB未満）を特定しました。")

    if not stub_articles:
        print("ℹ️ 修復対象のスタブ記事はありません。")
        sys.exit(0)

    # --- 4. AIによる優先度決定 (Top 3) ---
    print(f"\n--- [ステップ3: AIによる修復優先度の決定] ---")
    
    df_stub_data = create_placeholder_data(stub_articles)
    
    priority_result = select_priority_section_by_data(
        gemini_client, 
        df_stub_data, 
        CORPORATE_IDENTITY, 
        stub_articles
    )
    
    print(f"✅ AIが最優先で修復すべき記事を選定しました。")
    print(f"🥇 最優先記事: {priority_result['file_name']}")
    
    articles_to_regenerate = []
    try:
        priority_article_info = next(p for p in stub_articles if p['file_name'] == priority_result['file_name'])
        articles_to_regenerate.append(priority_article_info)
    except StopIteration:
        print(f"⚠️ AIが選んだ {priority_result['file_name']} がスタブリストにないため、先頭から修復します。")
        articles_to_regenerate = stub_articles[:DEFAULT_REPAIR_COUNT]
    else:
        remaining_stubs = [p for p in stub_articles if p['file_name'] != priority_result['file_name']]
        articles_to_regenerate.extend(remaining_stubs[:DEFAULT_REPAIR_COUNT - 1])

    print(f"\n--- [ステップ4: 優先度 Top {len(articles_to_regenerate)} 件のHTMLを再生成] ---")
    for i, plan in enumerate(articles_to_regenerate):
        print(f"  {i+1}. {plan['file_name']}")
        
    # --- 5. (本番) 既存ファイルのHTML修復・再生成 ---
    
    # ナビゲーション用に「サイト全体の計画」を渡す
    nav_list_for_generation = [
        {
            "file_name": p['file_name'], 
            "title": p['title'], 
            "purpose": p.get('generated_purpose', p.get('summary', p.get('purpose', '')))
        } for p in all_planned_articles
    ]
    
    for i, plan in enumerate(articles_to_regenerate):
        print(f"\n--- 🏭 [修復 {i+1}/{len(articles_to_regenerate)}] {plan['title']} ({plan['file_name']}) ---")

        target_page_for_generation = {
            'title': plan['title'],
            'file_name': plan['file_name'],
            'purpose': plan.get('generated_purpose', plan.get('summary', plan.get('purpose', '')))
        }
        
        if not target_page_for_generation['purpose']:
             print(f"⚠️ 警告: {plan['file_name']} の目的（Purpose）が計画書に見つかりません。AIが内容を推測します。")

        final_html_code = generate_single_page_html(
            gemini_client,
            target_page_for_generation, 
            CORPORATE_IDENTITY,
            None, 
            nav_list_for_generation,
            retry_attempts=3
        )
        
        if "❌" not in final_html_code:
            generate_file_path = os.path.join(BASE_DIR, plan['file_name'])
            os.makedirs(os.path.dirname(generate_file_path), exist_ok=True)
            try:
                with open(generate_file_path, "w", encoding="utf-8") as f:
                    f.write(final_html_code)
                print(f"✅ [修復完了] ファイル上書き成功: {generate_file_path}")
            except Exception as e:
                print(f"❌ [修復失敗] ファイル書き込みエラー: {e}")
        else:
             print(f"❌ [修復失敗] HTMLコード生成失敗: {plan['file_name']}")
             
    # --- 6. [追加] ハブページの自動更新 (WBS 5.5/5.6) ---
    print(f"\n--- [ステップ5: ハブページの自動更新] ---")
    
    # 6a. 更新すべきハブを特定 (修復された3件の親)
    parent_hub_paths = set()
    for plan in articles_to_regenerate: # 修復された3件
        parent_hub_paths.add(os.path.join(os.path.dirname(plan['file_name']), "index.html").replace(os.path.sep, '/'))

    print(f"🏭 以下のハブページを（必要に応じて）更新します: {parent_hub_paths}")

    for hub_path in parent_hub_paths:
        if not os.path.exists(os.path.join(BASE_DIR, hub_path)):
            print(f"ℹ️ ハブ {hub_path} が存在しないため、スキップします。")
            continue
            
        print(f"\n--- 🏭 [ハブ更新] {hub_path} ---")
        try:
            parent_page_info = next(p for p in all_planned_articles if p['file_name'] == hub_path)
        except StopIteration:
            print(f"❌ 警告: 計画リストに親ハブ ({hub_path}) が見つかりません。スキップします。")
            continue

        parent_page_info_for_regeneration = {
            'file_name': parent_page_info['file_name'],
            'title': parent_page_info['title'],
            'purpose': parent_page_info.get('generated_purpose', parent_page_info.get('summary')) 
        }

        # 6b. ハブ配下の「全」詳細記事をリストアップ
        hub_dir = os.path.dirname(hub_path)
        all_articles_in_section = []
        for plan in all_planned_articles:
             if (os.path.dirname(plan['file_name']) == hub_dir) and (plan['file_name'] != hub_path):
                all_articles_in_section.append(plan)

        print(f"  -> {len(all_articles_in_section)} 件の詳細記事（新旧含む）をスキャンしました。")

        # 6c. AIへの指示（Purpose）に「全記事リスト」を組み込む
        new_article_links_html = "<ul>"
        if not all_articles_in_section:
            new_article_links_html = "<p>（現在、このセクションの詳細記事はありません）</p>"
        else:
            for plan in all_articles_in_section: 
                link_path = os.path.basename(plan['file_name']) 
                article_summary = plan.get('generated_purpose', plan.get('summary', ''))
                new_article_links_html += f"<li><a href='{link_path}' class='text-blue-500 hover:underline'>{plan['title']}</a>: {article_summary}</li>"
            new_article_links_html += "</ul>"
        
        parent_page_info_for_regeneration['purpose'] = f"""
        このページ（{parent_page_info_for_regeneration['title']}）は、以下の「{len(all_articles_in_section)}件の全詳細記事」への導線を含むハブページとして機能します。
        元の目的（{parent_page_info_for_regeneration['purpose']}）を要約しつつ、これらの新しい記事への明確な導線（目次）を提供してください。

        【{hub_dir} セクションの全詳細記事リスト】
        {new_article_links_html}
        """
        
        # 6d. ハブページを再生成
        final_hub_code = generate_single_page_html(
            gemini_client,
            parent_page_info_for_regeneration, 
            CORPORATE_IDENTITY,
            None, 
            nav_list_for_generation, # (nav_list_for_generation は 5 で定義済み)
            retry_attempts=3
        )
        
        if "❌" not in final_hub_code:
            hub_file_path = os.path.join(BASE_DIR, parent_page_info_for_regeneration['file_name'])
            try:
                with open(hub_file_path, "w", encoding="utf-8") as f:
                    f.write(final_hub_code)
                print(f"✅ [ハブ更新完了] ファイルを上書き保存しました: {hub_file_path}")
            except Exception as e:
                print(f"❌ [ハブ更新失敗] ファイル書き込みエラー: {e}")
        else:
            print(f"❌ [ハブ更新失敗] HTMLの再生成に失敗しました。")


    print("\n--- 🛠️ HP 修復・再生成スクリプト 完了 ---")

if __name__ == "__main__":
    main()
