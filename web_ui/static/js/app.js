async function fetchJson(url, role = 'admin', options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-Role': role,
      ...(options.headers || {})
    }
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || `Request failed: ${response.status}`);
  }
  return data;
}

function listToHtml(items, mapper) {
  return items.length ? items.map(mapper).join('') : '<li>None.</li>';
}

async function runQuick(type, name, target) {
  const endpoint = `/api/${type}/${name}/execute`;
  const output = document.getElementById('quick-output');
  output.textContent = `Executing ${type}:${name}...`;

  try {
    const result = await fetchJson(endpoint, 'admin', {
      method: 'POST',
      body: JSON.stringify({ target })
    });
    output.textContent = JSON.stringify(result, null, 2);
  } catch (error) {
    output.textContent = `Execution error: ${error.message}`;
  }

  await refresh();
}

async function refresh() {
  try {
    const health = await fetchJson('/api/health', 'viewer');
    document.getElementById('health').textContent = JSON.stringify(health, null, 2);
    document.getElementById('health-inline').textContent = `Status: ${health.status} | Modules: ${health.module_count}`;

    const modules = await fetchJson('/api/modules', 'admin');
    document.getElementById('modules').innerHTML = listToHtml(
      modules.slice(0, 12),
      m => `<li><strong>${m.name}</strong> <em>(${m.category})</em></li>`
    );

    const pipelines = await fetchJson('/api/pipelines', 'admin');
    document.getElementById('pipelines').innerHTML = listToHtml(
      pipelines,
      p => `<li><strong>${p.name}</strong> - ${p.stages} stages</li>`
    );

    const workflows = await fetchJson('/api/workflows', 'admin');
    document.getElementById('workflows').innerHTML = listToHtml(
      workflows,
      w => `<li><strong>${w.name}</strong> - ${w.steps} steps</li>`
    );

    const jobs = await fetchJson('/api/jobs', 'admin');
    document.getElementById('jobs').innerHTML = listToHtml(
      jobs.slice(0, 20),
      j => `<li>#${j.job_id} <strong>${j.type}</strong>:${j.name}</li>`
    );
  } catch (error) {
    document.getElementById('health').textContent = `Dashboard refresh failed: ${error.message}`;
  }
}

document.getElementById('module-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  await runQuick('modules', document.getElementById('module-name').value, document.getElementById('module-target').value);
});

document.getElementById('pipeline-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  await runQuick('pipelines', document.getElementById('pipeline-name').value, document.getElementById('pipeline-target').value);
});

document.getElementById('workflow-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  await runQuick('workflows', document.getElementById('workflow-name').value, document.getElementById('workflow-target').value);
});

setInterval(refresh, 7000);
refresh();
