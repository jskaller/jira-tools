document.addEventListener('DOMContentLoaded', async () => {
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
});
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
const testBtn = document.getElementById('test-conn');
if (testBtn) {
  testBtn.addEventListener('click', async () => {
    const r = await fetch('/api/admin/test-connection');
    const j = await r.json();
    const msg = document.getElementById('admin-msg');
    if (msg) msg.textContent = j.configured ? 'Looks configured.' : 'Not configured.';
  });
}


(function(){
  const btn = document.getElementById('test-conn');
  if (!btn) return;
  btn.addEventListener('click', async () => {
    btn.disabled = true;
    const msg = document.getElementById('admin-msg');
    if (msg) msg.textContent = 'Testing...';
    try {
      const r = await fetch('/api/admin/test-connection');
      const j = await r.json();
      if (!j.configured) {
        msg.textContent = 'Not configured: ' + (j.error || 'Provide base URL, email, and token.');
      } else if (j.ok) {
        const who = (j.account && (j.account.displayName || j.account.emailAddress)) || 'OK';
        msg.textContent = 'Connected as ' + who;
      } else {
        msg.textContent = 'Connection failed: ' + (j.error || 'Unknown error');
      }
    } catch (e) {
      if (msg) msg.textContent = 'Connection failed: ' + e;
    } finally {
      btn.disabled = false;
    }
  });
})();
