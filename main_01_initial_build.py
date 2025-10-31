import os
import sys
import json
import shutil
from google import genai

# モジュールをインポート
from agents.agent_01_identity import generate_corporate_identity
from agents.agent_02_strategy import (
    generate_final_sitemap,
    generate_content_strategy,
    generate_target_page_list
)
from agents.agent_03_generation import generate_single_page_html

# --- 0. 設定 ---
OPINION_FILE = "config/opinion.txt"
REPORTS_DIR = "output_reports" # 👈 [追加] レポート保存先
OUTPUT_DIR = "output_website/PEOPLE-OPT-Unified-Site"
ZIP_FILENAME = "output_website/people_opt_site_unified.zip"

def setup_client():
    """Geminiクライアントを初期化"""
    try:
        # Colab環境を想定
        from google.colab import userdata
        GOOGLE_API_KEY = userdata.get('GEMINI_API_KEY')
        if not GOOGLE_API_KEY:
            raise ValueError("GEMINI_API_KEY が Colab Secrets に設定されていません。")
        return genai.Client(api_key=GOOGLE_API_KEY)
    except ImportError:
        # ローカル環境を想定
        GOOGLE_API_KEY = os.environ.get('GEMINI_API_KEY')
        if not GOOGLE_API_KEY:
            raise EnvironmentError("GEMINI_API_KEY が環境変数に設定されていません。")
        return genai.Client(api_key=GOOGLE_API_KEY)
    except Exception as e:
        print(f"❌ クライアント初期化エラー: {e}")
        return None

def main():
    print("--- 🚀 HP初回構築エージェント (フェーズ1-4) 開始 ---")

    # --- 0. クライアント初期化 ---
    gemini_client = setup_client()
    if gemini_client is None:
        sys.exit(1)

    # --- 1. 個人の意見をロード ---
    try:
        with open(OPINION_FILE, 'r', encoding='utf-8') as f:
            RAW_VISION_INPUT = f.read()
        print(f"✅ [フェーズ1] {OPINION_FILE} を読み込みました。")
    except Exception as e:
        print(f"❌ {OPINION_FILE} の読み込みに失敗: {e}")
        sys.exit(1)

    # --- 2. 法人格の生成 ---
    CORPORATE_IDENTITY = generate_corporate_identity(gemini_client, RAW_VISION_INPUT)
    print("✅ [フェーズ2] 法人格（Corporate Identity）を生成しました。")

    # --- 3. 戦略の生成 ---
    sitemap_result = generate_final_sitemap(gemini_client, CORPORATE_IDENTITY)
    content_strategy_result = generate_content_strategy(gemini_client, CORPORATE_IDENTITY, sitemap_result)
    TARGET_PAGES_LIST = generate_target_page_list(gemini_client, CORPORATE_IDENTITY, content_strategy_result)

    if not TARGET_PAGES_LIST:
        print("❌ ターゲットリストの生成に失敗したため、処理を中断します。")
        sys.exit(1)
    print("✅ [フェーズ3] サイト戦略とターゲットリストを生成しました。")

    # --- 🔽 [修正] 戦略レポートをファイルに保存 ---
    os.makedirs(REPORTS_DIR, exist_ok=True)
    try:
        with open(os.path.join(REPORTS_DIR, "01_corporate_identity.md"), 'w', encoding='utf-8') as f:
            f.write(CORPORATE_IDENTITY)
        with open(os.path.join(REPORTS_DIR, "02_sitemap.md"), 'w', encoding='utf-8') as f:
            f.write(sitemap_result)
        with open(os.path.join(REPORTS_DIR, "03_content_strategy.md"), 'w', encoding='utf-8') as f:
            f.write(content_strategy_result)

        # ターゲットリストもJSONで保存
        with open(os.path.join(REPORTS_DIR, "04_target_pages_list.json"), 'w', encoding='utf-8') as f:
            json.dump(TARGET_PAGES_LIST, f, indent=2, ensure_ascii=False)

        print(f"✅ [レポート] 法人格と戦略を {REPORTS_DIR} に保存しました。")
    except Exception as e:
        print(f"⚠️ [レポート] 戦略ファイルの保存中にエラー: {e}")
    # --- 🔼 [修正] ここまで ---

    # --- 4. 全体（ハブページ）の生成 ---
    print("\n--- [フェーズ4] 全体（ハブページ）のHTML生成を開始 ---")
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)

    generated_files = {}

    for page in TARGET_PAGES_LIST:
        print(f"\n--- 🏭 ページ生成: {page['title']} ({page['file_name']}) ---")

        final_html_code = generate_single_page_html(
            gemini_client,
            page,
            CORPORATE_IDENTITY,
            content_strategy_result,
            TARGET_PAGES_LIST,
            retry_attempts=3
        )

        if "❌" not in final_html_code:
            target_file_path = os.path.join(OUTPUT_DIR, page['file_name'])
            target_dir = os.path.dirname(target_file_path)
            os.makedirs(target_dir, exist_ok=True)

            try:
                with open(target_file_path, "w", encoding="utf-8") as f:
                    f.write(final_html_code)
                generated_files[page['file_name']] = f"✅ 生成完了: {target_file_path}"
            except Exception as e:
                generated_files[page['file_name']] = f"❌ ファイル書き込みエラー: {e}"
        else:
            generated_files[page['file_name']] = final_html_code

    print("\n--- 🎉 全ページ生成結果サマリー ---")
    for filename, status in generated_files.items():
        print(f"{filename.ljust(30)}: {status}")

    # --- ZIP化 ---
    print(f"\n--- 📦 {ZIP_FILENAME} にZIP圧縮中 ---")
    try:
        shutil.make_archive(ZIP_FILENAME.replace('.zip', ''), 'zip', OUTPUT_DIR)
        print(f"✅ ZIPファイルの作成が完了しました: {ZIP_FILENAME}")
    except Exception as e:
        print(f"❌ ZIPファイルの作成中にエラーが発生しました: {e}")

    print("--- 🚀 HP初回構築エージェント 完了 ---")

if __name__ == "__main__":
    main()
