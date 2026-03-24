async function fetchJson(url, role = 'admin') {
  const response = await fetch(url, { headers: { 'X-Role': role } });
  return response.json();
}

async function refresh() {
  const health = await fetchJson('/api/health', 'viewer');
  document.getElementById('health').textContent = JSON.stringify(health, null, 2);

  const modules = await fetchJson('/api/modules', 'admin');
  document.getElementById('modules').innerHTML = modules.slice(0, 10).map(m => `<li>${m.name} (${m.category})</li>`).join('');

  const pipelines = await fetchJson('/api/pipelines', 'admin');
  document.getElementById('pipelines').innerHTML = pipelines.map(p => `<li>${p.name} - ${p.stages} stages</li>`).join('');

  const jobs = await fetchJson('/api/jobs', 'admin');
  document.getElementById('jobs').innerHTML = jobs.slice(0, 10).map(j => `<li>#${j.job_id} ${j.type}:${j.name}</li>`).join('');
}

setInterval(refresh, 5000);
refresh();
