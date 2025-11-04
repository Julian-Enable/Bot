const jwt = require('jsonwebtoken');

// Create a JWT for the GitHub App using the private key (PEM) and APP_ID
function createAppJWT(appId, privateKey) {
  const now = Math.floor(Date.now() / 1000);
  const payload = {
    iat: now - 60,
    exp: now + (9 * 60), // 9 minutes
    iss: appId
  };
  return jwt.sign(payload, privateKey, { algorithm: 'RS256' });
}

async function getInstallationIdForRepo(jwtToken, owner, repo) {
  const url = `https://api.github.com/repos/${owner}/${repo}/installation`;
  const res = await fetch(url, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${jwtToken}`,
      Accept: 'application/vnd.github+json'
    }
  });
  if (res.status === 404) {
    const text = await res.text();
    throw new Error(`Installation not found for repo ${owner}/${repo}: ${text}`);
  }
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Failed to get installation id: ${res.status} ${text}`);
  }
  const j = await res.json();
  return j.id;
}

async function createInstallationToken(jwtToken, installationId) {
  const url = `https://api.github.com/app/installations/${installationId}/access_tokens`;
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${jwtToken}`,
      Accept: 'application/vnd.github+json'
    }
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Failed to create installation token: ${res.status} ${text}`);
  }
  const j = await res.json();
  return j.token;
}

async function getFile(owner, repo, path, branch, token) {
  const url = `https://api.github.com/repos/${owner}/${repo}/contents/${encodeURIComponent(path)}?ref=${encodeURIComponent(branch)}`;
  const res = await fetch(url, {
    method: 'GET',
    headers: {
      Authorization: `token ${token}`,
      Accept: 'application/vnd.github+json'
    }
  });
  if (res.status === 404) return null;
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Failed to get file: ${res.status} ${text}`);
  }
  return await res.json();
}

async function createOrUpdateFile(owner, repo, path, contentBuffer, message, branch, token, committer) {
  const existing = await getFile(owner, repo, path, branch, token);
  const body = {
    message,
    content: contentBuffer.toString('base64'),
    branch
  };
  if (committer) body.committer = committer;
  if (existing && existing.sha) body.sha = existing.sha;

  const url = `https://api.github.com/repos/${owner}/${repo}/contents/${encodeURIComponent(path)}`;
  const res = await fetch(url, {
    method: 'PUT',
    headers: {
      Authorization: `token ${token}`,
      Accept: 'application/vnd.github+json',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(body)
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Failed to create/update file: ${res.status} ${text}`);
  }
  return await res.json();
}

module.exports = {
  createAppJWT,
  getInstallationIdForRepo,
  createInstallationToken,
  getFile,
  createOrUpdateFile
};
