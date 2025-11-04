import os
import sys
from bs4 import BeautifulSoup

# --- 0. 設定 ---
BASE_DIR = "docs" 

# ⬇️ あなたのAdSenseスクリプト（client=... を含む）
ADSENSE_HEAD_TEMPLATE = """
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADSENSE_CLIENT_ID}"
     crossorigin="anonymous"></script>
"""

def main():
    # --- 1. AdSense IDの入力 ---
    ADSENSE_CLIENT_ID = input("Google AdSense Client ID (ca-pub-...) を入力してください: ")
    
    if not ADSENSE_CLIENT_ID.startswith("ca-pub-"):
        print(f"❌ エラー: AdSense ID ({ADSENSE_CLIENT_ID}) が 'ca-pub-' で始まっていません。処理を中断します。")
        sys.exit(1)
        
    print(f"--- 🏷️ AdSenseタグ ({ADSENSE_CLIENT_ID}) 挿入スクリプト開始 ---")

    # --- 2. サイトディレクトリのスキャン ---
    if not os.path.isdir(BASE_DIR):
        print(f"❌ サイトディレクトリ ({BASE_DIR}) が見つかりません。")
        sys.exit(1)
        
    files_processed = 0
    files_skipped = 0
    TARGET_EXTENSIONS = ('.html', '.htm')
    
    print(f"--- 🏭 {BASE_DIR} 配下の全HTMLファイルをスキャン・処理中 ---")

    for root, _, files in os.walk(BASE_DIR):
        for filename in files:
            if filename.lower().endswith(TARGET_EXTENSIONS):
                full_path = os.path.join(root, filename)
                
                try:
                    # 3. HTMLを読み込む
                    with open(full_path, 'r', encoding='utf-8') as f:
                        soup = BeautifulSoup(f, 'html.parser')

                    # 4. 既にタグがないか簡易チェック
                    if ADSENSE_CLIENT_ID in str(soup):
                        print(f"ℹ️ スキップ (AdSense ID検出済み): {full_path}")
                        files_skipped += 1
                        continue

                    # 5. <head> タグの挿入
                    if soup.head:
                        adsense_script_tag = BeautifulSoup(ADSENSE_HEAD_TEMPLATE.format(ADSENSE_CLIENT_ID=ADSENSE_CLIENT_ID), 'html.parser')
                        soup.head.append(adsense_script_tag) # <head>の末尾に追加
                    else:
                        print(f"⚠️ 警告: <head> タグなし (スキップ): {full_path}")
                        continue 

                    # 6. ファイルを上書き保存
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write(str(soup))
                        
                    print(f"✅ AdSenseタグ挿入完了: {full_path}")
                    files_processed += 1
                    
                except Exception as e:
                    print(f"❌ エラー ({full_path}): {e}")

    print(f"\n--- 🏷️ スクリプト完了 ---")
    print(f"✅ 合計 {files_processed} 件のHTMLファイルにAdSenseタグを挿入しました。")
    print(f"ℹ️ {files_skipped} 件のファイルは既にAdSenseタグが挿入されていたためスキップしました。")

if __name__ == "__main__":
    main()
