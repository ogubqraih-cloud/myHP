from http.server import BaseHTTPRequestHandler
import json
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
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length))
            messages = body.get('messages', [])

            message = client.messages.create(
                model='claude-sonnet-4-6',
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=messages,
            )
            text = message.content[0].text
            self._respond(200, {'text': text})

        except Exception as e:
            self._respond(500, {'error': 'エラーが発生しました。しばらくしてから再度お試しください。'})

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def _respond(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
