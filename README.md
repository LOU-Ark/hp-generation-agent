# hp-generation-agent

## 概要

このリポジトリは、大規模言語モデルを使用してWebコンテンツの生成と改善を行うために設計された、Pythonベースのエージェントシステムを含んでいます。エージェントは、法人格（コーポレートアイデンティティ）の定義、Webサイト戦略の策定、初期HTMLコンテンツの生成、および既存コンテンツの改善に焦点を当てています。

## 主な機能と利点

  * **法人格（コーポレートアイデンティティ）の定義:** 提供されたテキストに基づき、法人格（パーパス、ミッション、ビジョン）を生成します。
  * **Webサイト戦略の生成:** Webサイトの構造をガイドするための階層的なサイトマップを作成します。
  * **HTMLの生成:** ターゲットページの基本情報、法人格、サイトマップ戦略に基づき、HTMLページを生成します。
  * **コンテンツの改善:** 既存のHTMLコンテンツを分析し、構造的および意味的な改善を行います。

## 前提条件と依存関係

  * Python 3.7以上
  * `google-generative-ai` (Google Gemini API)
  * `beautifulsoup4`
  * `pandas`
  * Google Gemini APIへのアクセス（APIキーが設定済みであること）

必要な依存関係をpipでインストールします：

```bash
pip install google-generative-ai beautifulsoup4 pandas
```

## インストールとセットアップ手順

1.  **リポジトリをクローンします:**

    ```bash
    git clone https://github.com/LOU-Ark/hp-generation-agent.git
    cd hp-generation-agent
    ```

2.  **依存関係をインストールします:**

    ```bash
    pip install -r requirements.txt # requirements.txt が存在しない場合は、上記の依存関係を記載したファイルを作成してください
    ```

3.  **Google Gemini APIのセットアップ:**

      * Google AI StudioからAPIキーを取得します。

      * 環境変数 `GOOGLE_API_KEY` を設定します：

        ```bash
        export GOOGLE_API_KEY="YOUR_API_KEY"
        ```

4.  **エージェントの設定（オプション）:**

      * `config/` ディレクトリにある `opinion.txt` ファイルを修正し、法人格生成のための初期インプットを提供します。

## 使用例とAPIドキュメント

各エージェントの使用例は以下の通りです：

**1. 法人格の生成 (agent\_01\_identity.py):**

```python
import os
import google.generativeai as genai
from agents import agent_01_identity

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')
client = model.start_chat(history=[])

with open("config/opinion.txt", "r") as f:
    raw_input = f.read()

identity = agent_01_identity.generate_corporate_identity(client, raw_input)
print(identity)
```

**2. 戦略の生成 (agent\_02\_strategy.py):**

```python
import os
import google.generativeai as genai
from agents import agent_02_strategy

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')
client = model.start_chat(history=[])

# 'identity'が前のステップで生成されていると仮定
sitemap = agent_02_strategy.generate_final_sitemap(client, identity)
print(sitemap)
```

**3. HTMLの生成 (agent\_03\_generation.py):**

```python
import os
import google.generativeai as genai
from agents import agent_03_generation

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')
client = model.start_chat(history=[])

# 'identity' と 'sitemap' が前のステップで生成されていると仮定

# ページリストの例
page_list = [
    {"title": "Homepage", "file_name": "index.html"},
    {"title": "About Us", "file_name": "about.html"}
]

# ターゲットページの詳細 (page_listに含まれていることを確認)
target_page = {"title": "Homepage", "file_name": "index.html"}
strategy_full = sitemap # Markdown形式

html_content = agent_03_generation.generate_single_page_html(client, target_page, identity, strategy_full, page_list, GTM_ID="YOUR_GTM_ID")
print(html_content)

# 出力をファイルに保存
with open(target_page['file_name'], "w") as f:
    f.write(html_content)
```

**4. コンテンツの改善 (agent\_04\_improvement.py):**

```python
import os
from agents import agent_04_improvement

# 使用例:
file_path = "index.html"  # 分析したいHTMLファイルのパス
analysis = agent_04_improvement.analyze_article_structure(file_path)
print(analysis)

# 改善のための潜在的な使用例（上記のようにGeminiのセットアップが必要）
# improved_content = agent_04_improvement.improve_article_content(client, file_path, identity)
```

## 設定オプション

  * **`GOOGLE_API_KEY` 環境変数:** あなたのGoogle Gemini APIキー。
  * **`opinion.txt`:** 法人格生成プロセスのための初期インプット。
  * **`GTM_ID`:** Google Tag Manager ID（オプション）。生成されるHTMLにGTMスニペットを自動的に挿入します。

## コントリビューション（貢献）ガイドライン

コントリビューションを歓迎します！貢献するには：

1.  リポジトリをフォーク（Fork）します。
2.  機能追加またはバグ修正のための新しいブランチを作成します。
3.  変更を加えます。
4.  プルリクエスト（Pull Request）を送信します。

コードが既存のスタイルに準拠し、適切なテストが含まれていることを確認してください。

## ライセンス情報

[ライセンスをここに記載] - 例: MIT License, Apache 2.0 License など。ライセンスがない場合は、追加を検討してください。

## 謝辞

  * Google AI (Gemini API)
  * 不可欠なライブラリを提供してくれたPythonコミュニティ
