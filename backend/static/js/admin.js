// admin.js v6
console.log('[admin.js v5] loaded');
document.addEventListener('DOMContentLoaded', () => {
  console.log('[admin.js v5] DOM ready');
  // Populate settings from backend (for non-secret fields)
  fetch('/api/admin/settings').then(r => r.json()).then(s => {
    for (const k of ['jira_base_url','jira_email','jql_default','bh_start','bh_end','max_issues','updated_days_limit']) {
      const el = document.querySelector(`[name="${k}"]`);
      if (el && (s[k] ?? '') !== '') el.value = s[k];
    }
    const toggle = document.getElementById('use_real_jira');
    if (toggle) toggle.checked = !!s.use_real_jira;
  });

  const form = document.getElementById('admin-form');
  const msg = document.getElementById('admin-msg');
  const testBtn = document.getElementById('test-conn');

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const fd = new FormData(form);
      const payload = Object.fromEntries(fd.entries());
      payload.use_real_jira = document.getElementById('use_real_jira')?.checked || false;
      for (const k of ['bh_start','bh_end','max_issues','updated_days_limit']) {
        if (k in payload) payload[k] = Number(payload[k]);
      }
      const res = await fetch('/api/admin/settings', {
        method: 'PUT',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        msg.textContent = 'Saved. Reloading…'; setTimeout(()=>location.reload(), 300);
      } else {
        let t = 'Failed to save';
        try { const j = await res.json(); if (j?.error) t += ': ' + j.error; } catch {}
        msg.textContent = t;
      }
    });
  }

  if (testBtn) {
    testBtn.addEventListener('click', async () => {
      console.log('[admin.js v5] Test connection clicked');
      testBtn.disabled = true;
      msg.textContent = 'Testing...';
      const base_url = document.querySelector('[name="jira_base_url"]')?.value?.trim();
      const email = document.querySelector('[name="jira_email"]')?.value?.trim();
      const token = document.querySelector('[name="jira_token"]')?.value || '';
      const body = { jira_base_url: base_url, jira_email: email, jira_token: token };
      try {
        const r = await fetch('/api/admin/test-connection', {
          method: 'POST',
          headers: {'Content-Type':'application/json'},
          body: JSON.stringify(body)
        });
        const j = await r.json();
        console.log('[admin.js v5] Test response', j);
        if (!j.configured) {
          msg.textContent = 'Not configured: ' + (j.error || 'Missing fields');
        } else if (j.ok) {
          const who = (j.account && (j.account.displayName || j.account.emailAddress)) || 'OK';
          msg.textContent = 'Connected as ' + who;
        } else {
          msg.textContent = 'Connection failed: ' + (j.error || 'Unknown error');
        }
      } catch (e) {
        console.error(e);
        msg.textContent = 'Connection failed: ' + e;
      } finally {
        testBtn.disabled = false;
      }
    });
  } else {
    console.warn('[admin.js v5] test-conn button not found');
  }
});
