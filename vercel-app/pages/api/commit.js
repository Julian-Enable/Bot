// API route to trigger a commit to the target repo using GitHub App installation token
// Expects ENV: APP_ID, PRIVATE_KEY, TARGET_REPO (owner/repo), BOT_BRANCH, COMMIT_NAME, COMMIT_EMAIL
// Rate limit: max 7 commits per UTC day (tracked in-memory, resets on redeploy or daily)

const { createAppJWT, getInstallationIdForRepo, createInstallationToken, getFile, createOrUpdateFile } = require('../../lib/githubApp');

// In-memory rate limit tracker (resets on serverless cold start or daily)
let dailyCommits = { date: null, count: 0 };

function normalizePrivateKey(key) {
  if (!key) return null;
  // if the key was pasted with escaped newlines, convert them
  return key.includes('-----BEGIN') ? key : key.replace(/\\n/g, '\n');
}

function checkRateLimit() {
  const today = new Date().toISOString().slice(0, 10); // YYYY-MM-DD
  if (dailyCommits.date !== today) {
    dailyCommits = { date: today, count: 0 };
  }
  if (dailyCommits.count >= 7) {
    return { ok: false, message: `Rate limit: max 7 commits per day reached (${dailyCommits.count}/7)` };
  }
  dailyCommits.count++;
  return { ok: true, remaining: 7 - dailyCommits.count };
}

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).end('Method not allowed');

  // Simple invocation secret to avoid open abuse. Set INVOCATION_SECRET in Vercel and send X-APP-KEY header.
  const invocationSecret = process.env.INVOCATION_SECRET;
  if (invocationSecret) {
    const header = req.headers['x-app-key'] || '';
    if (!header || header !== invocationSecret) {
      return res.status(401).json({ error: 'Unauthorized (missing X-APP-KEY)' });
    }
  }

  // Check rate limit
  const rateLimitCheck = checkRateLimit();
  if (!rateLimitCheck.ok) {
    return res.status(429).json({ error: rateLimitCheck.message });
  }

  const APP_ID = process.env.APP_ID;
  const PRIVATE_KEY_RAW = process.env.PRIVATE_KEY;
  const TARGET_REPO = process.env.TARGET_REPO; // owner/repo
  const BOT_BRANCH = process.env.BOT_BRANCH || 'contrib-bot';
  const COMMIT_NAME = process.env.COMMIT_NAME || 'contrib-bot';
  const COMMIT_EMAIL = process.env.COMMIT_EMAIL || 'noreply@github.com';

  if (!APP_ID || !PRIVATE_KEY_RAW || !TARGET_REPO) {
    return res.status(500).json({ error: 'Server misconfigured: APP_ID, PRIVATE_KEY and TARGET_REPO required' });
  }

  try {
    const privateKey = normalizePrivateKey(PRIVATE_KEY_RAW);
    const jwt = createAppJWT(APP_ID, privateKey);
    const [owner, repo] = TARGET_REPO.split('/');
    const installationId = await getInstallationIdForRepo(jwt, owner, repo);
    const installToken = await createInstallationToken(jwt, installationId);

    // file path and update behavior: append a timestamped line, avoid duplicate per UTC day
    const path = 'contributions/keep_alive.md';
    const branch = BOT_BRANCH;

    const existing = await getFile(owner, repo, path, branch, installToken);
    let newContent = '';
    const now = new Date().toISOString().replace('+00:00', 'Z');
    const line = `- ${now}\n`;
    if (existing && existing.content) {
      const buf = Buffer.from(existing.content, 'base64');
      const text = buf.toString('utf-8');
      const lines = text.split(/\r?\n/).filter(Boolean);
      if (lines.length) {
        const last = lines[lines.length - 1];
        // try parse ISO after '- '
        if (last.startsWith('- ')) {
          const ts = last.slice(2).trim().replace(/Z$/, '');
          try {
            const lastDate = new Date(ts);
            const nowDate = new Date(now);
            if (lastDate.getUTCFullYear() === nowDate.getUTCFullYear() && lastDate.getUTCMonth() === nowDate.getUTCMonth() && lastDate.getUTCDate() === nowDate.getUTCDate()) {
              return res.status(200).json({ ok: true, message: 'Already committed today (UTC)', branch });
            }
          } catch (e) {
            // ignore parse error and append
          }
        }
      }
      newContent = text + '\n' + line;
    } else {
      newContent = line;
    }

    const result = await createOrUpdateFile(owner, repo, path, Buffer.from(newContent, 'utf8'), `chore: daily contribution ${now}`, branch, installToken, { name: COMMIT_NAME, email: COMMIT_EMAIL });
    return res.status(200).json({ ok: true, result, rateLimit: { remaining: rateLimitCheck.remaining, max: 7 } });
  } catch (err) {
    console.error(err);
    // rollback rate limit counter on error
    if (dailyCommits.count > 0) dailyCommits.count--;
    return res.status(500).json({ error: String(err) });
  }
}
