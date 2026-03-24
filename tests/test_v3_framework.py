from api.app import create_app
from modules import build_module_registry


def test_module_count():
    assert len(build_module_registry()) >= 22


def test_health_endpoint():
    app = create_app()
    client = app.test_client()
    res = client.get('/api/health')
    assert res.status_code == 200


def test_pipeline_list_endpoint():
    app = create_app()
    client = app.test_client()
    res = client.get('/api/pipelines', headers={'X-Role': 'admin'})
    assert res.status_code == 200
    data = res.get_json()
    names = {p['name'] for p in data}
    assert 'full_pentest_pipeline' in names
