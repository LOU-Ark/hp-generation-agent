import pandas as pd
import numpy as np

def create_placeholder_data(target_articles):
    """全記事のファイル名をインデックスとし、ダミーのパフォーマンスDFを生成する。"""
    data = {}
    for item in target_articles:
        file_name_key = item['file_name']
        title = item['title']
        data[file_name_key] = {
            'CVR': 1.5, 'ReadRate_90': 30, 'Keywords': 'データ欠損',
            'Total_Sessions_30D': 2500, 'Article_Title': title
        }
    df_all_data = pd.DataFrame.from_dict(data, orient='index').set_index('Article_Title')
    df_all_data.index.name = 'Article_Title'
    return df_all_data
