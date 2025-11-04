// API route to return the last commit timestamp (UTC) from contributions/keep_alive.md
const { createAppJWT, getInstallationIdForRepo, createInstallationToken, getFile } = require('../../lib/githubApp');

function normalizePrivateKey(key) {
  if (!key) return null;
  return key.includes('-----BEGIN') ? key : key.replace(/\\n/g, '\n');
}

export default async function handler(req, res) {
  if (req.method !== 'GET') return res.status(405).end('Method not allowed');

  const APP_ID = process.env.APP_ID;
  const PRIVATE_KEY_RAW = process.env.PRIVATE_KEY;
  const TARGET_REPO = process.env.TARGET_REPO; // owner/repo
  const BOT_BRANCH = process.env.BOT_BRANCH || 'contrib-bot';

  if (!APP_ID || !PRIVATE_KEY_RAW || !TARGET_REPO) {
    return res.status(500).json({ error: 'Server misconfigured: APP_ID, PRIVATE_KEY and TARGET_REPO required' });
  }

  try {
    const privateKey = normalizePrivateKey(PRIVATE_KEY_RAW);
    const jwt = createAppJWT(APP_ID, privateKey);
    const [owner, repo] = TARGET_REPO.split('/');
    const installationId = await getInstallationIdForRepo(jwt, owner, repo);
    const installToken = await createInstallationToken(jwt, installationId);

    const path = 'contributions/keep_alive.md';
    const existing = await getFile(owner, repo, path, BOT_BRANCH, installToken);
    if (!existing || !existing.content) return res.status(200).json({ ok: true, last: null });
    const buf = Buffer.from(existing.content, 'base64');
    const text = buf.toString('utf-8');
    const lines = text.split(/\r?\n/).filter(Boolean);
    if (!lines.length) return res.status(200).json({ ok: true, last: null });
    const last = lines[lines.length - 1];
    return res.status(200).json({ ok: true, last });
  } catch (err) {
    console.error(err);
    return res.status(500).json({ error: String(err) });
  }
}
