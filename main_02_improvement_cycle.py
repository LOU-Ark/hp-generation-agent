import os
import sys
import json
import shutil
from google import genai
# from IPython.display import display, Markdown # .pyファイルからは削除

# モジュールをインポート
from agents.agent_04_improvement import (
    analyze_article_structure,
    generate_article_purpose,
    select_priority_section_by_data,
    generate_priority_article_titles
)
from utils.file_utils import (
    get_existing_article_count,
    integrate_content_data,
    save_to_markdown
)
from utils.analysis_utils import create_placeholder_data

# --- 0. 設定 ---
BASE_DIR = "output_website/PEOPLE-OPT-Unified-Site" # 分析対象（フェーズ4の出力）
REPORTS_DIR = "output_reports"
REPORT_FILE = os.path.join(REPORTS_DIR, "planned_articles.md")
DEFAULT_ARTICLE_COUNT = 3

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
    """
    (仮) 法人格をロードする。
    実際には main_01 の出力（例: JSONファイル）からロードすべきだが、
    ここでは main_01 を再実行して取得する簡易的な方法をとる。
    """
    try:
        from agents.agent_01_identity import generate_corporate_identity
        with open("config/opinion.txt", 'r', encoding='utf-8') as f:
            RAW_VISION_INPUT = f.read()
        client = setup_client() # このためだけにクライアントを起動
        if client:
            # generate_corporate_identity は print するので、ここでは出力を抑制
            # print("法人格を再生成しています...")
            return generate_corporate_identity(client, RAW_VISION_INPUT)
        else:
            raise Exception("クライアントの初期化に失敗")
    except Exception as e:
        print(f"警告: 法人格の動的ロードに失敗: {e}。ダミーを使用します。")
        return "パーパス: データによる個人の生活最適化。 トーン: 論理的、先進的。"


def main():
    print("--- 🔄 HP改善サイクルエージェント (フェーズ5-6) 開始 ---")

    # --- 0. クライアント初期化 ---
    gemini_client = setup_client()
    if gemini_client is None:
        sys.exit(1)

    # --- (前提) 法人格の取得 ---
    CORPORATE_IDENTITY = load_corporate_identity()
    print("✅ 法人格をロードしました。")

    # --- 5a. 戦略（AS-IS分析） ---
    print("\n--- [フェーズ5a: AS-IS分析] 既存サイトをスキャン中 ---")
    processed_articles = []
    TARGET_EXTENSIONS = ('.html', '.htm')

    if not os.path.isdir(BASE_DIR):
        print(f"❌ 分析対象ディレクトリ {BASE_DIR} が見つかりません。")
        print("先に main_01_initial_build.py を実行してください。")
        sys.exit(1)

    for root, _, files in os.walk(BASE_DIR):
        for filename in files:
            if filename.lower().endswith(TARGET_EXTENSIONS):
                full_path = os.path.join(root, filename)
                article_data, error = analyze_article_structure(full_path)

                if article_data:
                    purpose = generate_article_purpose(gemini_client, article_data, CORPORATE_IDENTITY)
                    processed_articles.append({
                        "file_name": os.path.relpath(full_path, BASE_DIR).replace(os.path.sep, '/'),
                        "title": article_data['page_title'],
                        "generated_purpose": purpose
                    })
                    print(f"✅ {processed_articles[-1]['file_name'].ljust(40)}: Purpose生成完了。")
                else:
                    print(f"❌ {filename.ljust(40)}: {error}")

    print(f"\n✅ [フェーズ5a 完了] 合計 {len(processed_articles)} 件の目的を定義しました。")

    # --- 5b. 戦略的優先度の決定 ---
    print("\n--- [フェーズ5b: 戦略的優先度の決定] AIが分析中 ---")
    df_all_data = create_placeholder_data(processed_articles)
    priority_result = select_priority_section_by_data(gemini_client, df_all_data, CORPORATE_IDENTITY, processed_articles)

    priority_file = priority_result['file_name']
    priority_section_info = next(p for p in processed_articles if p['file_name'] == priority_file)

    print(f"✅ [フェーズ5b 完了] 最優先セクションが決定しました。")
    print(f"🥇 最優先セクション: {priority_section_info['title']} (`{priority_file}`)")
    print(f"🔑 選定理由: {priority_result['reason']}")

    # --- 6. 詳細記事の企画・生成 ---
    print("\n--- [フェーズ6: 詳細記事の企画・生成] AIが企画中 ---")
    start_number = get_existing_article_count(BASE_DIR) + 1
    error_msg, article_plans = generate_priority_article_titles(
        gemini_client, priority_section_info, CORPORATE_IDENTITY, DEFAULT_ARTICLE_COUNT, start_number
    )

    if not article_plans:
        print(f"❌ 記事の企画に失敗しました: {error_msg}")
        sys.exit(1)

    print(f"✅ [フェーズ6 完了] {len(article_plans)} 件の新規記事を企画しました。")

    # --- 7. (シミュレーション) ファイル生成と全体計画の保存 ---
    print("\n--- [最終処理: ファイル生成シミュレーションと計画保存] ---")

    # フォルダパスを修正し、ファイル名を 'file_name' に統一
    generate_file_list_paths = []
    for i, plan in enumerate(article_plans):
        target_dir = os.path.dirname(priority_section_info['file_name'])
        file_name = os.path.join(target_dir, plan.get('file_name', f'error-slug-{i}.html'))
        file_name = file_name.replace(os.path.sep, '/')

        # article_plans 自体を正しいパスに更新
        article_plans[i]['file_name'] = file_name
        generate_file_list_paths.append(file_name)

    # (シミュレーション) ファイルをtouch
    for file_name in generate_file_list_paths:
        generate_file_path = os.path.join(BASE_DIR, file_name)
        os.makedirs(os.path.dirname(generate_file_path), exist_ok=True)
        try:
            with open(generate_file_path, 'w', encoding='utf-8') as f:
                f.write(f"<html><title>{plan['title']}</title><body><h1>{plan['title']}</h1><p>{plan['summary']}</p></body></html>")
            print(f"✅ (シミュレーション) ファイル作成成功: {generate_file_path}")
        except Exception as e:
            print(f"❌ (シミュレーション) ファイル作成失敗: {e}")

    # (レポート) 全体計画をMDファイルに保存
    os.makedirs(REPORTS_DIR, exist_ok=True)
    all_content_plans = integrate_content_data(processed_articles, article_plans)
    save_to_markdown(all_content_plans, REPORT_FILE)

    print(f"✅ 全体計画を {REPORT_FILE} に保存しました。")
    print("--- 🔄 HP改善サイクルエージェント 完了 ---")

if __name__ == "__main__":
    main()
