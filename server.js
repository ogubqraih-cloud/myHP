import Anthropic from '@anthropic-ai/sdk';
import express from 'express';
import { readFileSync, existsSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

// .env ファイルを手動読み込み（dotenv 依存を避けるため）
const __dir = dirname(fileURLToPath(import.meta.url));
const envPath = join(__dir, '.env');
if (existsSync(envPath)) {
  const lines = readFileSync(envPath, 'utf8').split('\n');
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const idx = trimmed.indexOf('=');
    if (idx === -1) continue;
    const key = trimmed.slice(0, idx).trim();
    const val = trimmed.slice(idx + 1).trim().replace(/^["']|["']$/g, '');
    if (key && !process.env[key]) process.env[key] = val;
  }
}

const client = new Anthropic();
const app = express();

app.use(express.json());
app.use(express.static(__dir));

const SYSTEM_PROMPT = `あなたは株式会社TechVisionのAIアシスタントです。
AIコンサルティングとIT支援サービスの案内、お問い合わせ対応を行います。
丁寧でプロフェッショナルな日本語で回答してください。

【対応できること】
- AIコンサルティング（LLM導入、AI戦略策定、業務自動化）に関する質問
- IT支援・DX推進（システム化、クラウド移行、セキュリティ）に関する質問
- サービス内容・進め方の概要説明
- お問い合わせ・相談の案内

【対応できないこと】
- 具体的な料金・見積もり → 「担当者からご連絡します」とお伝えし、ページ下部のお問い合わせフォームへ誘導
- 詳細なプロジェクト契約内容 → 同上
- 他社サービスとの比較評価

回答は簡潔に、必要に応じて箇条書きを活用してください。`;

app.post('/api/chat', async (req, res) => {
  const { messages } = req.body;

  if (!Array.isArray(messages) || messages.length === 0) {
    return res.status(400).json({ error: 'messages は必須です' });
  }

  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');

  try {
    const stream = client.messages.stream({
      model: 'claude-sonnet-4-6',
      max_tokens: 1024,
      system: SYSTEM_PROMPT,
      messages,
    });

    for await (const event of stream) {
      if (
        event.type === 'content_block_delta' &&
        event.delta.type === 'text_delta'
      ) {
        res.write(`data: ${JSON.stringify({ text: event.delta.text })}\n\n`);
      }
    }

    res.write('data: [DONE]\n\n');
    res.end();
  } catch (err) {
    console.error('Claude API エラー:', err.message);
    res.write(`data: ${JSON.stringify({ error: 'エラーが発生しました。しばらくしてから再度お試しください。' })}\n\n`);
    res.write('data: [DONE]\n\n');
    res.end();
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`サーバー起動: http://localhost:${PORT}`);
});
