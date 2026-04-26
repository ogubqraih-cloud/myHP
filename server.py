import os
import json
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response, send_from_directory
import anthropic

load_dotenv()

client = anthropic.Anthropic()
app = Flask(__name__, static_folder=".", static_url_path="")

SYSTEM_PROMPT = """あなたは「AI導入サービス　支援」のAIアシスタントです。
以下の自社情報をもとに、訪問者からの質問に丁寧かつ正確に回答してください。

━━━━━━━━━━━━━━━━━━━━
【サービス名】
AI導入サービス　支援

【サービス内容】
AIサービスコンサルティング

【料金】
月額1万円

【営業時間・連絡先】
24時間対応
お問い合わせ: xxxtest.example.com

【よくある質問と回答】
Q: 料金は？
A: 月額1万円です。

Q: 解約方法は？
A: お問い合わせいただければ対応いたします。解約をご希望の場合はメールアドレスをご案内しますので、お気軽にご連絡ください。
━━━━━━━━━━━━━━━━━━━━

【回答のルール】
- ユーザーが質問した内容にのみ答える
- 質問されていない情報（料金・問い合わせ先・他のFAQなど）は自分から出さない
- 回答は簡潔に、質問に直接関係する情報だけを返す
- 丁寧でプロフェッショナルな日本語で回答する
- 上記に記載のない詳細を聞かれた場合のみ「担当者よりご連絡します」とお伝えする"""


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    messages = data.get("messages", [])
    if not messages:
        return {"error": "messages は必須です"}, 400

    def generate():
        try:
            with client.messages.stream(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    yield f"data: {json.dumps({'text': text}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': 'エラーが発生しました。しばらくしてから再度お試しください。'}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def static_files(path):
    if path and (Path(app.static_folder) / path).exists():
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    print(f"サーバー起動: http://localhost:{port}")
    app.run(port=port, debug=False)
