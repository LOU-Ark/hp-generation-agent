import os
import sys
from datetime import datetime
from utils.file_utils import load_markdown_table_to_list

# --- 設定 ---
BASE_URL = "https://LOU-Ark.github.io/hp-generation-agent"
PLAN_FILE = "output_reports/planned_articles.md"
OUTPUT_FILE = "docs/sitemap.xml"

def generate_sitemap():
    print(f"--- 🗺️ サイトマップ生成エージェント (main_04) 開始 ---")
    
    # 1. 計画ファイルを読み込む
    print(f"--- [ステップ1] 計画ファイル ({PLAN_FILE}) を読み込み中 ---")
    if not os.path.exists(PLAN_FILE):
        print(f"❌ 計画ファイル ({PLAN_FILE}) が見つかりません。")
        print("   main_01 または main_02 を実行して計画を生成してください。")
        sys.exit(1)
        
    all_planned_articles = load_markdown_table_to_list(PLAN_FILE)
    if not all_planned_articles:
        print(f"❌ 計画ファイルの読み込みに失敗しました。")
        sys.exit(1)
    
    print(f"✅ 計画(To-Be): {len(all_planned_articles)} 件のタスクを読み込みました。")

    # 2. XMLコンテンツの生成
    print(f"--- [ステップ2] XMLコンテンツを生成中 ---")
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    # 今日の日付
    lastmod = datetime.now().strftime('%Y-%m-%d')
    
    for page in all_planned_articles:
        file_name = page.get('file_name')
        if not file_name:
            continue
            
        # index.html の場合は / で終わる美しいURLに
        if file_name == "index.html":
            loc = f"{BASE_URL}/"
        elif file_name.endswith("index.html"):
            #例: "vision/index.html" -> "https"//.../vision/
            loc = f"{BASE_URL}/{os.path.dirname(file_name)}/"
        else:
            #例: "legal/privacy-policy.html" -> "https"//.../legal/privacy-policy.html
            loc = f"{BASE_URL}/{file_name}"
            
        xml_content += "  <url>\n"
        xml_content += f"    <loc>{loc}</loc>\n"
        xml_content += f"    <lastmod>{lastmod}</lastmod>\n"
        xml_content += "  </url>\n"

    xml_content += "</urlset>\n"

    # 3. ファイルに保存
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(xml_content)
        print(f"✅ [完了] サイトマップを {OUTPUT_FILE} に保存しました。")
    except Exception as e:
        print(f"❌ ファイル書き込みエラー: {e}")

if __name__ == "__main__":
    # ⬇️ [修正] 'main()' ではなく 'generate_sitemap()' を呼び出す
    generate_sitemap()
