"""V2 limits and frozen retention cases."""

import pytest
import test_cern_dimuon_qualification as q

from research.cern_dimuon_qualification.admission.ledger import StoreV2

for name in dir(q):
    if name.startswith(
        ("test_store_", "test_inventory_", "test_enumeration_", "test_failed_root_")
    ):
        globals()[name] = getattr(q, name)


@pytest.fixture(autouse=True)
def v2(monkeypatch):
    monkeypatch.setattr(q, "Store", StoreV2)
    monkeypatch.setattr(q, "audit_existing", StoreV2.audit_existing)


def test_v2_limits(tmp_path):
    store = StoreV2(tmp_path / "v2")
    store.write("records/source", "full", bytes(294912))
    for key, data in (("records/source", b"x"), ("input", bytes(4161537))):
        with pytest.raises(q.Hold):
            store.write(key, "extra", data)
    store.audit_existing(store.root)
    with pytest.raises(TypeError):
        store.budget["input"] = 1
    with pytest.raises(q.Hold):
        store.finish("../escape", {})
    (store.root / "stray").touch()
    with pytest.raises(q.Hold):
        store.audit()
    store.finish("supervisor", {"state": "HOLD"})
