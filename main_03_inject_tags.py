import os
import sys
from bs4 import BeautifulSoup

# --- 0. 設定 ---
BASE_DIR = "docs" 

# GTMスニペットのテンプレート
GTM_HEAD_TEMPLATE = """
<script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':
new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
}})(window,document,'script','dataLayer','{GTM_ID}');</script>
"""

GTM_BODY_TEMPLATE = """
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={GTM_ID}"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
"""

# AdSenseスニペットのテンプレート
ADSENSE_HEAD_TEMPLATE = """
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADSENSE_CLIENT_ID}"
     crossorigin="anonymous"></script>
"""

def main():
    # --- 1. IDの入力 ---
    GTM_ID = input("Google Tag Manager ID (GTM-XXXXXXX) を入力してください (スキップはEnter): ").strip()
    ADSENSE_CLIENT_ID = input("Google AdSense Client ID (ca-pub-...) を入力してください (スキップはEnter): ").strip()

    if not GTM_ID and not ADSENSE_CLIENT_ID:
        print("❌ GTM ID と AdSense ID の両方が入力されませんでした。処理を終了します。")
        sys.exit(1)

    if GTM_ID and not GTM_ID.startswith("GTM-"):
        print(f"⚠️ 警告: GTM ID ({GTM_ID}) が 'GTM-' で始まっていません。")
    if ADSENSE_CLIENT_ID and not ADSENSE_CLIENT_ID.startswith("ca-pub-"):
        print(f"⚠️ 警告: AdSense ID ({ADSENSE_CLIENT_ID}) が 'ca-pub-' で始まっていません。")

    GTM_ID = GTM_ID or None
    ADSENSE_CLIENT_ID = ADSENSE_CLIENT_ID or None
        
    print(f"--- 🏷️ タグ挿入スクリプト (GTM: {GTM_ID}, AdSense: {ADSENSE_CLIENT_ID}) 開始 ---")

    # --- 2. サイトディレクトリのスキャン ---
    if not os.path.isdir(BASE_DIR):
        print(f"❌ サイトディレクトリ ({BASE_DIR}) が見つかりません。")
        sys.exit(1)
        
    files_processed_gtm = 0
    files_processed_adsense = 0
    files_skipped_gtm = 0
    files_skipped_adsense = 0
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
                    
                    modified = False # ファイルが変更されたか追跡

                    # 4. GTMタグの挿入
                    if GTM_ID:
                        if GTM_ID in str(soup):
                            files_skipped_gtm += 1
                        elif soup.head and soup.body:
                            # GTM Head
                            gtm_script_tag = BeautifulSoup(GTM_HEAD_TEMPLATE.format(GTM_ID=GTM_ID), 'html.parser')
                            soup.head.insert(0, gtm_script_tag)
                            # GTM Body
                            gtm_noscript_tag = BeautifulSoup(GTM_BODY_TEMPLATE.format(GTM_ID=GTM_ID), 'html.parser')
                            soup.body.insert(0, gtm_noscript_tag)
                            files_processed_gtm += 1
                            modified = True
                        else:
                            print(f"⚠️ 警告: GTM挿入スキップ (<head>または<body>なし): {full_path}")

                    # 5. AdSenseタグの挿入
                    if ADSENSE_CLIENT_ID:
                        if ADSENSE_CLIENT_ID in str(soup):
                            files_skipped_adsense += 1
                        elif soup.head:
                            adsense_script_tag = BeautifulSoup(ADSENSE_HEAD_TEMPLATE.format(ADSENSE_CLIENT_ID=ADSENSE_CLIENT_ID), 'html.parser')
                            soup.head.append(adsense_script_tag) # <head>の末尾に追加
                            files_processed_adsense += 1
                            modified = True
                        else:
                            print(f"⚠️ 警告: AdSense挿入スキップ (<head>なし): {full_path}")

                    # 6. ファイルを上書き保存 (変更があった場合のみ)
                    if modified:
                        with open(full_path, 'w', encoding='utf-8') as f:
                            f.write(str(soup))
                        print(f"✅ タグ挿入完了: {full_path}")
                    
                except Exception as e:
                    print(f"❌ エラー ({full_path}): {e}")

    print(f"\n--- 🏷️ スクリプト完了 ---")
    if GTM_ID:
        print(f"✅ GTM: {files_processed_gtm} 件に挿入しました。(スキップ: {files_skipped_gtm} 件)")
    if ADSENSE_CLIENT_ID:
        print(f"✅ AdSense: {files_processed_adsense} 件に挿入しました。(スキップ: {files_skipped_adsense} 件)")

if __name__ == "__main__":
    main()
