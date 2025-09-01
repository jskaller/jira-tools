document.addEventListener('DOMContentLoaded', async () => {
  const el = document.getElementById('chart');
  if (!el) return;
  // Extract report_id from URL (last segment)
  const parts = window.location.pathname.split('/').filter(Boolean);
  const reportId = parts[parts.length - 1];
  const res = await fetch(`/api/reports/${reportId}`);
  if (!res.ok) return;
  const data = await res.json();
  const ctx = el.getContext('2d');
  if (window.Chart) {
    new Chart(ctx, {
      type: 'bar',
      data: {
        labels: data.issues,
        datasets: [{label: 'Issues', data: data.issues.map(_=>1)}]
      }
    });
  } else {
    const container = document.getElementById('chart-container');
    if (container) container.innerHTML = '<div class="text-muted">Chart.js not loaded.</div>';
  }
});
