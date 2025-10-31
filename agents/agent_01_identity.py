import json
from google import genai

def generate_corporate_identity(client, raw_input):
    """
    提供されたRAWテキストに基づき、法人格をGeminiに生成させる。
    """
    prompt = f"""
    あなたは企業のアイデンティティ構築の専門家です。
    以下の「法人の核となる哲学とビジョン」を総合的に分析し、この法人の核となる「法人格（パーパス、ミッション、ビジョン）」を定義してください。

    【重要】分析以外の言葉や、対話的な応答、説明は一切せず、要求されたフォーマットの抽出結果のみを Markdown で出力してください。

    ### 法人の核となる哲学とビジョン
    {raw_input}

    ---

    ### 抽出・生成すべき法人格フレームワーク

    **パーパス (存在意義):** [最も根源的な存在理由と社会への貢献を簡潔に定義]
    **ミッション (現在の使命・行動指針):** [パーパスを達成するために、現在具体的に行うべき使命を定義]
    **ビジョン (目指す未来像):** [ミッションが達成された先に実現したい、具体的で鼓舞される未来の姿を定義]
    **法人格/トーン:** [この法人が対外的に持つべき個性、ブランドイメージ、コミュニケーションのトーンを定義]
    """

    print("Geminiモデルで哲学テキストを分析し、法人格を形成しています...")
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        print(f"法人格が生成されました。")
        return response.text.strip()
    except Exception as e:
        print(f"❌ 法人格の形成中にエラーが発生しました: {e}")
        return f"❌ 法人格の形成中にエラーが発生しました: {e}"
