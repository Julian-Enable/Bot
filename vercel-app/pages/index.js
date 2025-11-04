import { useState, useEffect } from 'react';

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState('');
  const [appKey, setAppKey] = useState('');
  const [status, setStatus] = useState(null);

  async function trigger() {
    setLoading(true);
    setMsg('');
    try {
      const headers = { 'Content-Type': 'application/json' };
      if (appKey) headers['X-APP-KEY'] = appKey;
      const res = await fetch('/api/commit', {
        method: 'POST',
        headers
      });
      const j = await res.json();
      if (res.ok) setMsg(JSON.stringify(j)); else setMsg('Error: ' + JSON.stringify(j));
      await fetchStatus(appKey);
    } catch (e) {
      setMsg('Fetch error: ' + String(e));
    } finally {
      setLoading(false);
    }
  }

  async function fetchStatus(key) {
    try {
      const headers = {};
      if (key) headers['X-APP-KEY'] = key;
      const res = await fetch('/api/status', { headers });
      const j = await res.json();
      if (res.ok) setStatus(j); else setStatus({ error: j });
    } catch (e) {
      setStatus({ error: String(e) });
    }
  }

  useEffect(() => {
    fetchStatus(appKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <main style={{ fontFamily: 'system-ui, Arial', padding: 24 }}>
      <h1>Contrib Bot (Vercel)</h1>
      <p>Hace commits diarios en una repo objetivo usando un GitHub App.</p>

      <div style={{ marginBottom: 12 }}>
        <label style={{ display: 'block', marginBottom: 6 }}>Invocation secret (X-APP-KEY) — opcional</label>
        <input value={appKey} onChange={(e) => setAppKey(e.target.value)} style={{ padding: 8, width: 360 }} />
      </div>

      <button onClick={trigger} disabled={loading} style={{ padding: '8px 12px' }}>
        {loading ? 'Enviando...' : 'Commit ahora'}
      </button>

      <section style={{ marginTop: 16 }}>
        <h3>Estado</h3>
        <pre>{status ? JSON.stringify(status, null, 2) : 'Cargando...'}</pre>
      </section>

      <section style={{ marginTop: 24 }}>
        <h3>Notas</h3>
        <ul>
          <li>Configura en Vercel: <code>APP_ID</code>, <code>PRIVATE_KEY</code>, <code>TARGET_REPO</code>, <code>COMMIT_NAME</code>, <code>COMMIT_EMAIL</code>.</li>
          <li>Opcional: <code>BOT_BRANCH</code> (por defecto <code>contrib-bot</code>).</li>
          <li>Si pones <code>INVOCATION_SECRET</code>, puedes pegarlo arriba en "Invocation secret" para que la UI lo envíe como <code>X-APP-KEY</code>.</li>
        </ul>
      </section>
      <pre style={{ marginTop: 16 }}>{msg}</pre>
    </main>
  );
}
