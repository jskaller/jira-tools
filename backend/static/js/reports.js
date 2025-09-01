async function loadReports() {
  const res = await fetch('/api/reports');
  const list = await res.json();
  const root = document.getElementById('reports-list');
  if (!root) return;
  root.innerHTML = '';
  for (const r of list) {
    const item = document.createElement('div');
    item.className = 'card';
    item.innerHTML = `<div class="card-body d-flex justify-content-between align-items-center">
      <div><strong>${r.name}</strong><div class="text-muted small">${r.created_at}</div></div>
      <div class="d-flex gap-2">
        <a class="btn btn-sm btn-outline-primary" href="/reports/${r.id}">Open</a>
        <button class="btn btn-sm btn-outline-danger" data-id="${r.id}">Delete</button>
      </div>
    </div>`;
    const btn = item.querySelector('button');
    if (btn) {
      btn.addEventListener('click', async (e) => {
        await fetch('/api/reports/'+e.target.dataset.id, {method:'DELETE'});
        loadReports();
      });
    }
    root.appendChild(item);
  }
}
document.addEventListener('DOMContentLoaded', loadReports);
const createBtn = document.getElementById('create-report');
if (createBtn) {
  createBtn.addEventListener('click', async () => {
    const name = prompt('Report name?');
    if (!name) return;
    const r = await fetch('/api/reports', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({name})});
    if (r.ok) loadReports();
  });
}
