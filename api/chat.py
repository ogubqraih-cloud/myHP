from http.server import BaseHTTPRequestHandler
import json
import os
from anthropic import Anthropic

client = Anthropic()

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


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(content_length))
        messages = body.get('messages', [])

        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        try:
            with client.messages.stream(
                model='claude-sonnet-4-6',
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    data = f"data: {json.dumps({'text': text}, ensure_ascii=False)}\n\n"
                    self.wfile.write(data.encode('utf-8'))
                    self.wfile.flush()
        except Exception as e:
            error = json.dumps({'error': 'エラーが発生しました。しばらくしてから再度お試しください。'}, ensure_ascii=False)
            self.wfile.write(f"data: {error}\n\n".encode('utf-8'))

        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
