import os
import pandas as pd
import re
import json

def load_markdown_table_to_list(file_path):
    """
    Markdownファイルからテーブルを読み込み、目的の辞書リスト形式に変換する。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Pandas DataFrame を使って読み込む
        lines = content.strip().split('\n')
        header_line = next(line for line in lines if line.startswith('|') and 'ファイル名' in line)
        data_lines = [line for line in lines if line.startswith('|') and '---|---' not in line and 'ファイル名' not in line]

        headers = [h.strip().replace('**', '') for h in header_line.strip('|').split('|')]
        data = [[c.strip().replace('**', '') for c in row.strip('|').split('|')] for row in data_lines]

        df = pd.DataFrame(data, columns=headers)

        # 目的のキーにリネーム
        df = df.rename(columns={
            'ファイル名': 'file_name',
            'タイトル': 'title',
            '生成された目的': 'generated_purpose',
            '概要・目的': 'summary'
        })

        return df.to_dict(orient='records')

    except Exception as e:
        print(f"❌ Markdown読み込みエラー: {e}")
        return None

def save_to_markdown(data_list, output_filename="planned_articles_summary.md"):
    """辞書のリストを受け取り、Markdown形式のテーブルとしてファイルに保存する。"""
    if not data_list:
        print("💡 リストが空のため、ファイルは生成されませんでした。")
        return

    try:
        df = pd.DataFrame(data_list)
        df = df.rename(columns={
            'title': 'タイトル',
            'summary': '概要・目的',
            'generated_purpose': '概要・目的',
            'file_name': 'ファイル名'
        })

        # カラムの順序を整える
        if '概要・目的' in df.columns:
            df = df[['ファイル名', 'タイトル', '概要・目的']]
        else:
            df = df[['ファイル名', 'タイトル']]

        markdown_table = df.to_markdown(index=False)

        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write("## 📜 コンテンツ全体計画 (既存 + 新規)\n\n")
            f.write(markdown_table)

        print(f"✅ 成功: Markdownファイル '{output_filename}' が作成されました。")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

def integrate_content_data(existing_articles, new_article_plans):
    """既存記事と計画記事を統合し、統一形式のリストを生成する。"""

    transformed_articles = []
    for item in existing_articles:
        transformed_articles.append({
            'title': item['title'],
            'summary': item.get('generated_purpose', item.get('purpose')), # 両方のキーに対応
            'file_name': item['file_name']
        })

    # new_article_plans も 'title', 'summary', 'file_name' の形式に統一されている前提

    all_planned_articles = transformed_articles + new_article_plans
    return all_planned_articles

def get_existing_article_count(base_dir):
    """指定されたフォルダ以下のHTMLファイル数 (index.htmlを除く) を返す。"""
    count = 0
    if not os.path.isdir(base_dir):
        return 0
    for root, _, files in os.walk(base_dir):
        for filename in files:
            if filename.lower().endswith(('.html', '.htm')) and filename.lower() != 'index.html':
                count += 1
    return count

def get_next_article_number(section_folder, base_dir):
    """
    指定されたセクションフォルダをスキャンし、既存の 'article-X.html' の最大連番+1を返す。
    """
    path_to_scan = os.path.join(base_dir, section_folder)
    if not os.path.exists(path_to_scan):
        return 1
    max_num = 0
    pattern = re.compile(r"article-(\d+)\.html", re.IGNORECASE)
    for filename in os.listdir(path_to_scan):
        match = pattern.match(filename)
        if match:
            try:
                current_num = int(match.group(1))
                if current_num > max_num:
                    max_num = current_num
            except ValueError:
                continue
    return max_num + 1
