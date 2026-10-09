from pathlib import Path
import time
from unittest.mock import patch

from PIL import Image
import pytest

from backend.app.gallery_index import GalleryIndex, contained_path


@pytest.fixture
def index(tmp_path):
    source = tmp_path / 'images'
    source.mkdir()
    Image.new('RGBA', (40, 80), (20, 40, 80, 90)).save(source / 'a.png')
    result = GalleryIndex(source, tmp_path / 'thumbs', tmp_path / 'index.db')
    result.refresh(force=True, wait=True)
    yield result
    result.close()


def test_warm_snapshot_does_not_scan(index):
    with patch.object(Path, 'iterdir', side_effect=AssertionError('Unexpected filesystem scan')):
        assert index.snapshot()['images'] == ['a.png']


def test_cold_snapshot_waits_for_initial_scan(tmp_path):
    source = tmp_path / 'images'
    source.mkdir()
    Image.new('RGBA', (40, 80), (20, 40, 80, 90)).save(source / 'cold.png')
    index = GalleryIndex(source, tmp_path / 'thumbs', tmp_path / 'index.db')
    try:
        assert index.snapshot()['images'] == ['cold.png']
    finally:
        index.close()


def test_missing_and_returning_file_preserve_added(index):
    original = index.snapshot()['image_meta']['a.png']
    source = index.source / 'a.png'
    content = source.read_bytes()
    source.unlink()
    index.refresh(force=True, wait=True)
    assert index.snapshot()['images'] == []
    source.write_bytes(content)
    index.refresh(force=True, wait=True)
    assert index.snapshot()['image_meta']['a.png']['added'] == original['added']


def test_scan_failure_keeps_snapshot(index):
    version = index.snapshot()['version']
    with patch.object(Path, 'iterdir', side_effect=PermissionError('offline')):
        index.refresh(force=True, wait=True)
    assert index.snapshot()['version'] == version
    assert index.status()['error'] == 'offline'


def test_revision_and_transparency(index):
    before = index.snapshot()['image_meta']['a.png']
    index._build('a.png', before)
    target, revision = index.derivative('a.png', 320)
    with Image.open(target) as image:
        assert image.size == (40, 80)
        assert 'A' in image.getbands()
    time.sleep(.01)
    Image.new('RGB', (100, 60), 'red').save(index.source / 'a.png')
    index.refresh(force=True, wait=True)
    assert index.snapshot()['image_meta']['a.png']['revision'] != revision


@pytest.mark.parametrize('name', ['../secret', '/outside', 'C:\\secret', '..\\secret', 'a:stream'])
def test_containment(index, name):
    with pytest.raises(ValueError):
        contained_path(index.source, name)


def test_gallery_contract_and_recovery(client, monkeypatch, index):
    from backend.app import legacy_runtime as legacy
    monkeypatch.setattr(legacy, 'gallery_index', index)
    monkeypatch.setattr(legacy, 'GALLERY_DIR', index.source)
    created = client.post('/api/gallery/groups', json={'name': 'Recovery', 'images': ['a.png']})
    assert created.status_code == 201
    group_id = created.json['id']
    original = (index.source / 'a.png').read_bytes()
    (index.source / 'a.png').unlink()
    index.refresh(force=True, wait=True)
    group = next(g for g in client.get('/api/gallery?groups=1').json['groups'] if g['id'] == group_id)
    assert group['image_count'] == 0 and group['cover_image'] is None
    (index.source / 'a.png').write_bytes(original)
    index.refresh(force=True, wait=True)
    group = next(g for g in client.get('/api/gallery/groups').json if g['id'] == group_id)
    assert group['image_paths'] == ['a.png']
    response = client.get('/api/gallery')
    assert client.get('/api/gallery', headers={'If-None-Match': response.headers['ETag']}).status_code == 304
    assert client.post('/api/gallery/groups', json={'name': 'Invalid', 'images': ['a.png', 'missing.png']}).status_code == 400
    assert client.post('/api/gallery/groups', json=[]).status_code == 400
    assert client.post('/api/gallery/groups/999999/images', json={'images': ['a.png']}).status_code == 404
    assert client.put('/api/gallery/groups/' + str(group_id), json={'cover_image': 'missing.png'}).status_code == 400
    assert client.get('/gallery/groups/' + created.json['slug']).status_code == 200
    assert client.post('/api/gallery/groups/' + str(group_id) + '/images/remove', json={'images': ['a.png']}).status_code == 200
    assert (index.source / 'a.png').exists()
