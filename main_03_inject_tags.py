import os
import sys
import re # ⬅️ [追加] 正規表現ライブラリをインポート
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
        
    files_processed = 0
    TARGET_EXTENSIONS = ('.html', '.htm')
    
    print(f"--- 🏭 {BASE_DIR} 配下の全HTMLファイルをスキャン・処理中 ---")

    for root, _, files in os.walk(BASE_DIR):
        for filename in files:
            if filename.lower().endswith(TARGET_EXTENSIONS):
                full_path = os.path.join(root, filename)
                
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        soup = BeautifulSoup(f, 'html.parser')
                    
                    modified = False 
                    
                    if not soup.head or not soup.body:
                         print(f"⚠️ 警告: <head>または<body>タグなし (スキップ): {full_path}")
                         continue

                    # --- ⬇️ [修正] 3. 既存のタグをすべて削除 ---
                    
                    # 既存のAdSenseタグを削除
                    if ADSENSE_CLIENT_ID:
                        existing_adsense = soup.head.find_all("script", {"src": re.compile(f"adsbygoogle.js.*{ADSENSE_CLIENT_ID}")})
                        for tag in existing_adsense:
                            tag.extract()
                            modified = True
                            
                    # 既存のGTM <head> タグを削除
                    if GTM_ID:
                        existing_gtm_head = soup.head.find_all("script", string=re.compile(f"dataLayer','{GTM_ID}'"))
                        for tag in existing_gtm_head:
                            tag.extract()
                            modified = True
                    
                    # 既存のGTM <body> タグを削除
                    if GTM_ID:
                        existing_gtm_body = soup.body.find_all("noscript", string=re.compile(f"id={GTM_ID}"))
                        for tag in existing_gtm_body:
                            tag.extract()
                            modified = True
                    # --- ⬆️ [修正] ここまで ---

                    # --- 4. AdSenseタグの挿入 (最優先: 0番目) ---
                    if ADSENSE_CLIENT_ID:
                        adsense_script_tag = BeautifulSoup(ADSENSE_HEAD_TEMPLATE.format(ADSENSE_CLIENT_ID=ADSENSE_CLIENT_ID), 'html.parser')
                        soup.head.insert(0, adsense_script_tag) # ⬅️ 先頭(0番目)に挿入
                        modified = True

                    # --- 5. GTMタグの挿入 (2番目) ---
                    if GTM_ID:
                        # GTM Head (AdSenseの次、つまり1番目に挿入)
                        gtm_script_tag = BeautifulSoup(GTM_HEAD_TEMPLATE.format(GTM_ID=GTM_ID), 'html.parser')
                        insert_position = 1 if ADSENSE_CLIENT_ID else 0 # AdSenseがあれば1番目
                        soup.head.insert(insert_position, gtm_script_tag) 
                        
                        # GTM Body (0番目)
                        gtm_noscript_tag = BeautifulSoup(GTM_BODY_TEMPLATE.format(GTM_ID=GTM_ID), 'html.parser')
                        soup.body.insert(0, gtm_noscript_tag)
                        
                        modified = True

                    # --- 6. ファイルを上書き保存 (変更があった場合のみ) ---
                    if modified:
                        with open(full_path, 'w', encoding='utf-8') as f:
                            f.write(str(soup))
                        print(f"✅ タグ挿入/修正完了: {full_path}")
                        files_processed += 1
                    
                except Exception as e:
                    print(f"❌ エラー ({full_path}): {e}")

    print(f"\n--- 🏷️ スクリプト完了 ---")
    print(f"✅ 合計 {files_processed} 件のHTMLファイルにタグを挿入/修正しました。")

if __name__ == "__main__":
    main()
