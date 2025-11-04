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
STUB_FILE_SIZE_THRESHOLD = 1024 
DEFAULT_REPAIR_COUNT = 3 

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
    identity_file = os.path.join(REPORTS_DIR, "01_corporate_identity.md")
    try:
        with open(identity_file, 'r', encoding='utf-8') as f:
            identity = f.read()
        print(f"✅ 法人格を {identity_file} から読み込みました。")
        return identity
    except Exception as e:
        print(f"❌ 法人格ファイル ({identity_file}) の読み込みに失敗: {e}")
        try:
            from agents.agent_01_identity import generate_corporate_identity
            with open("config/opinion.txt", 'r', encoding='utf-8') as f:
                RAW_VISION_INPUT = f.read()
            client = setup_client() 
            if client:
                print("⚠️ [フォールバック] 法人格をAPIで再生成します。")
                return generate_corporate_identity(client, RAW_VISION_INPUT)
            else:
                raise Exception("クライアントの初期化に失敗")
        except Exception as e_fallback:
            print(f"❌ 代替処理も失敗: {e_fallback}。ダミーを使用します。")
            return "パーパス: データによる個人の生活最適化。 トーン: 論理的、先進的。"

def main():
    
    # --- 1. IDの入力 ---
    GTM_ID = input("Google Tag Manager ID (GTM-XXXXXXX) を入力してください (スキップはEnter): ")
    ADSENSE_CLIENT_ID = input("Google AdSense Client ID (ca-pub-...) を入力してください (スキップはEnter): ")
    
    if GTM_ID and not GTM_ID.startswith("GTM-"):
        print(f"⚠️ 警告: GTM ID ({GTM_ID}) が 'GTM-' で始まっていません。")
    if ADSENSE_CLIENT_ID and not ADSENSE_CLIENT_ID.startswith("ca-pub-"):
        print(f"⚠️ 警告: AdSense ID ({ADSENSE_CLIENT_ID}) が 'ca-pub-' で始まっていません。")

    GTM_ID = GTM_ID or None # 空文字ならNone
    ADSENSE_CLIENT_ID = ADSENSE_CLIENT_ID or None # 空文字ならNone
        
    print(f"--- 🛠️ HP 修復・再生成スクリプト (GTM: {GTM_ID}, AdSense: {ADSENSE_CLIENT_ID}) 開始 ---")
    
    # --- 2. クライアント初期化と法人格の取得 ---
    gemini_client = setup_client()
    if gemini_client is None: sys.exit(1)
    CORPORATE_IDENTITY = load_corporate_identity()

    # --- 3. 計画(To-Be)の読み込み ---
    print(f"\n--- [ステップ1: 計画(To-Be)の読み込み] ---")
    if not os.path.exists(PLAN_FILE):
        print(f"❌ 計画ファイル ({PLAN_FILE}) が見つかりません。")
        sys.exit(1)
    all_planned_articles = load_markdown_table_to_list(PLAN_FILE)
    if not all_planned_articles:
        print(f"❌ 計画ファイルの読み込みに失敗しました。")
        sys.exit(1)
    print(f"✅ 計画(To-Be): {len(all_planned_articles)} 件のタスクを読み込みました。")

    # --- 4. 修復対象（スタブ）の検出 ---
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
    
    articles_to_regenerate = []
    if not stub_articles:
        print("ℹ️ 修復対象のスタブ記事はありません。")
        print("   ただし、ハブページ (index.html) のタグを更新します。")
    else:
        # --- 5. AIによる優先度決定 (Top 3) ---
        print(f"\n--- [ステップ3: AIによる修復優先度の決定] ---")
        df_stub_data = create_placeholder_data(stub_articles)
        priority_result = select_priority_section_by_data(
            gemini_client, df_stub_data, CORPORATE_IDENTITY, stub_articles
        )
        print(f"🥇 最優先記事: {priority_result['file_name']}")
        
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

    # --- 6. (本番) スタブファイルのHTML修復・再生成 ---
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
        
        final_html_code = generate_single_page_html(
            gemini_client,
            target_page_for_generation, 
            CORPORATE_IDENTITY,
            None, 
            nav_list_for_generation,
            GTM_ID, 
            ADSENSE_CLIENT_ID, # ⬅️ [追加] AdSense IDを渡す
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
             
    # --- 7. ハブページのタグも更新 ---
    print(f"\n--- [ステップ5: ハブページのGTM/AdSenseタグ自動更新] ---")
    
    hub_paths_to_update = [
        p['file_name'] for p in all_planned_articles if p['file_name'].endswith('index.html')
    ]
    print(f"🏭 {len(hub_paths_to_update)} 件のハブページ (index.html) のタグを更新します...")

    for hub_path in hub_paths_to_update:
        print(f"\n--- 🏭 [ハブタグ更新] {hub_path} ---")
        try:
            parent_page_info = next(p for p in all_planned_articles if p['file_name'] == hub_path)
        except StopIteration:
            print(f"❌ 警告: 計画リストに親ハブ ({hub_path}) が見つかりません。スキップします。")
            continue

        parent_page_info_for_regeneration = {
            'file_name': parent_page_info['file_name'],
            'title': parent_page_info['title'],
            'purpose': parent_page_info.get('generated_purpose', parent_page_info.get('summary', '')) 
        }

        original_purpose = parent_page_info_for_regeneration['purpose']
        parent_page_info_for_regeneration['purpose'] = f"""
        【最重要タスク】GTM ID ({GTM_ID}) と AdSense Client ID ({ADSENSE_CLIENT_ID}) を <head> と <body> の正しい位置に挿入してください。
        
        【コンテンツの目的】
        {original_purpose}
        (もしこれがハブページなら、配下の記事へのリンク目次も自動で生成してください)
        """
        
        final_hub_code = generate_single_page_html(
            gemini_client,
            parent_page_info_for_regeneration, 
            CORPORATE_IDENTITY,
            None, 
            nav_list_for_generation,
            GTM_ID, 
            ADSENSE_CLIENT_ID, # ⬅️ [追加] AdSense IDを渡す
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
