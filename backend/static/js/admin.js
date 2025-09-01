console.log('[admin.js] loaded');
document.addEventListener('DOMContentLoaded', async () => {
  console.log('[admin.js] DOM ready');
  const res = await fetch('/api/admin/settings');
  if (res.ok) {
    const s = await res.json();
    for (const k of ['jira_base_url','jira_email','jql_default','bh_start','bh_end','max_issues','updated_days_limit']) {
      const el = document.querySelector(`[name="${k}"]`);
      if (el) el.value = s[k] ?? '';
    }
    const toggle = document.getElementById('use_real_jira');
    if (toggle) toggle.checked = !!s.use_real_jira;
  }

  const adminForm = document.getElementById('admin-form');
  if (adminForm) {
    adminForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      const payload = Object.fromEntries(fd.entries());
      const toggle = document.getElementById('use_real_jira');
      payload.use_real_jira = toggle ? toggle.checked : false;
      for (const k of ['bh_start','bh_end','max_issues','updated_days_limit']) {
        if (k in payload) payload[k] = Number(payload[k]);
      }
      const res = await fetch('/api/admin/settings', {method:'PUT', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
      const msg = document.getElementById('admin-msg');
      if (msg) msg.textContent = res.ok ? 'Saved.' : 'Failed to save';
    });
  }

  const btn = document.getElementById('test-conn');
  const msg = document.getElementById('admin-msg');
  if (!btn) { console.warn('[admin.js] test-conn button not found'); return; }
  btn.addEventListener('click', async () => {
    console.log('[admin.js] Test connection clicked');
    btn.disabled = true;
    if (msg) msg.textContent = 'Testing...';
    try {
      const r = await fetch('/api/admin/test-connection');
      const j = await r.json().catch(()=>({ok:false,error:'Bad JSON'}));
      console.log('[admin.js] Test response', j);
      if (!j.configured) {
        if (msg) msg.textContent = 'Not configured: ' + (j.error || 'Provide base URL, email, token.');
      } else if (j.ok) {
        const who = (j.account && (j.account.displayName || j.account.emailAddress)) || 'OK';
        if (msg) msg.textContent = 'Connected as ' + who;
      } else {
        if (msg) msg.textContent = 'Connection failed: ' + (j.error || 'Unknown error');
      }
    } catch (e) {
      if (msg) msg.textContent = 'Connection failed: ' + e;
      console.error(e);
    } finally {
      btn.disabled = false;
    }
  });
});
