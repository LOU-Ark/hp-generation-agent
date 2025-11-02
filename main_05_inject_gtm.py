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

def main():
    # --- 1. GTM IDの入力 ---
    GTM_ID = input("Google Tag Manager ID (GTM-XXXXXXX) を入力してください: ")
    
    if not GTM_ID.startswith("GTM-"):
        print(f"❌ エラー: GTM ID ({GTM_ID}) が 'GTM-' で始まっていません。処理を中断します。")
        sys.exit(1)
        
    print(f"--- 🏷️ GTMタグ ({GTM_ID}) 挿入スクリプト開始 ---")
    
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

                    # 4. 既にタグがないか簡易チェック (あればスキップ)
                    # (GTM ID自体がスープに含まれていたら、既に処理済みとみなす)
                    if GTM_ID in str(soup):
                        print(f"ℹ️ スキップ (GTM ID検出済み): {full_path}")
                        files_skipped += 1
                        continue

                    # 5. <head> タグの挿入
                    if soup.head:
                        gtm_script_tag = BeautifulSoup(GTM_HEAD_TEMPLATE.format(GTM_ID=GTM_ID), 'html.parser')
                        soup.head.insert(0, gtm_script_tag)
                    else:
                        print(f"⚠️ 警告: <head> タグなし (スキップ): {full_path}")
                        continue 

                    # 6. <body> タグの挿入
                    if soup.body:
                        gtm_noscript_tag = BeautifulSoup(GTM_BODY_TEMPLATE.format(GTM_ID=GTM_ID), 'html.parser')
                        soup.body.insert(0, gtm_noscript_tag)
                    else:
                        print(f"⚠️ 警告: <body> タグなし (スキップ): {full_path}")
                        continue 

                    # 7. ファイルを上書き保存
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write(str(soup))
                        
                    print(f"✅ GTMタグ挿入完了: {full_path}")
                    files_processed += 1
                    
                except Exception as e:
                    print(f"❌ エラー ({full_path}): {e}")

    print(f"\n--- 🏷️ スクリプト完了 ---")
    print(f"✅ 合計 {files_processed} 件のHTMLファイルにGTMタグを挿入しました。")
    print(f"ℹ️ {files_skipped} 件のファイルは既にGTMタグが挿入されていたためスキップしました。")

if __name__ == "__main__":
    main()
