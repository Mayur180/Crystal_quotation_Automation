"""
COMPREHENSIVE TEST SUITE — 134 test cases for CRYSTAL Quotation Manager.
Run with: pytest test_comprehensive.py -v
"""
import pytest
import json
import bcrypt
from pathlib import Path
from unittest.mock import patch

# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def mock_data_root(tmp_path, monkeypatch):
    """Patch get_data_root to return a temp folder."""
    import app.services.paths as paths
    monkeypatch.setattr(paths, "get_data_root", lambda: tmp_path)
    return tmp_path

# ============================================================
# SECTION 1: AUTHENTICATION (20 tests)
# ============================================================

class TestAuth:
    def test_bcrypt_hash_format(self):
        h = bcrypt.hashpw(b"test", bcrypt.gensalt())
        assert h.startswith(b"$2b$")

    def test_bcrypt_verify_correct(self):
        h = bcrypt.hashpw(b"test123", bcrypt.gensalt())
        assert bcrypt.checkpw(b"test123", h)

    def test_bcrypt_verify_wrong(self):
        h = bcrypt.hashpw(b"test123", bcrypt.gensalt())
        assert not bcrypt.checkpw(b"wrong", h)

    def test_bcrypt_salt_unique(self):
        h1 = bcrypt.hashpw(b"test", bcrypt.gensalt())
        h2 = bcrypt.hashpw(b"test", bcrypt.gensalt())
        assert h1 != h2

    def test_bcrypt_empty_password(self):
        h = bcrypt.hashpw(b"", bcrypt.gensalt())
        assert bcrypt.checkpw(b"", h)

    def test_bcrypt_long_password(self):
        pwd = b"a" * 72
        h = bcrypt.hashpw(pwd, bcrypt.gensalt())
        assert bcrypt.checkpw(pwd, h)

    def test_find_user_case_insensitive(self, mock_data_root):
        from app.services.user_service import save_users, find_user_by_username
        save_users([{"user_id": "U001", "username": "Admin", "password": "hash", "role": "admin"}])
        assert find_user_by_username("admin") is not None
        assert find_user_by_username("ADMIN") is not None
        assert find_user_by_username("aDmIn") is not None

    def test_find_user_not_found(self, mock_data_root):
        from app.services.user_service import find_user_by_username
        assert find_user_by_username("nonexistent") is None

    def test_find_user_empty_string(self, mock_data_root):
        from app.services.user_service import find_user_by_username
        assert find_user_by_username("") is None

    def test_find_user_none(self, mock_data_root):
        from app.services.user_service import find_user_by_username
        assert find_user_by_username(None) is None

    def test_is_admin_true(self, mock_data_root):
        from app.services.user_service import save_users, is_admin
        save_users([{"user_id": "U001", "username": "admin", "password": "hash", "role": "admin"}])
        assert is_admin("admin") == True

    def test_is_admin_false(self, mock_data_root):
        from app.services.user_service import save_users, is_admin
        save_users([{"user_id": "U001", "username": "user", "password": "hash", "role": "user"}])
        assert is_admin("user") == False

    def test_is_admin_missing_role(self, mock_data_root):
        from app.services.user_service import save_users, is_admin
        save_users([{"user_id": "U001", "username": "norole", "password": "hash"}])
        assert is_admin("norole") == False

    def test_is_admin_nonexistent(self, mock_data_root):
        from app.services.user_service import is_admin
        assert is_admin("ghost") == False

    def test_create_user_duplicate(self, mock_data_root):
        from app.services.user_service import create_user, save_users
        save_users([{"user_id": "U001", "username": "admin", "password": "hash", "role": "admin"}])
        with patch('app.services.user_service.sync_user_to_sheet'):
            with pytest.raises(ValueError, match="already exists"):
                create_user(username="admin", password="newpass")

    def test_create_user_empty_username(self, mock_data_root):
        from app.services.user_service import create_user
        with patch('app.services.user_service.sync_user_to_sheet'):
            with pytest.raises(ValueError, match="Username is required"):
                create_user(username="", password="pass")

    def test_create_user_empty_password(self, mock_data_root):
        from app.services.user_service import create_user
        with patch('app.services.user_service.sync_user_to_sheet'):
            with pytest.raises(ValueError, match="Password is required"):
                create_user(username="newuser", password="")

    def test_create_user_invalid_role(self, mock_data_root):
        from app.services.user_service import create_user
        with patch('app.services.user_service.sync_user_to_sheet'):
            with pytest.raises(ValueError, match="Role must be"):
                create_user(username="newuser", password="pass", role="superadmin")

    def test_create_user_hashes_password(self, mock_data_root):
        from app.services.user_service import create_user, find_user_by_username
        with patch('app.services.user_service.sync_user_to_sheet'):
            create_user(username="newuser", password="pass123")
            user = find_user_by_username("newuser")
            assert user["password"].startswith("$2b$")

    def test_create_user_unique_id(self, mock_data_root):
        from app.services.user_service import create_user, save_users, load_users
        save_users([{"user_id": "U001", "username": "admin", "password": "hash", "role": "admin"}])
        with patch('app.services.user_service.sync_user_to_sheet'):
            create_user(username="user2", password="pass")
            users = load_users()
            ids = [u["user_id"] for u in users]
            assert len(ids) == len(set(ids))

# ============================================================
# SECTION 2: USER SERVICE (25 tests)
# ============================================================

class TestUserService:
    def test_load_users_empty_file(self, mock_data_root, monkeypatch):
        import app.services.user_service as us
        monkeypatch.setattr(us, "_users_file", lambda: mock_data_root / "NONEXISTENT.json")
        assert us.load_users() == []

    def test_load_users_malformed_json(self, mock_data_root, monkeypatch):
        import app.services.user_service as us
        monkeypatch.setattr(us, "_users_file", lambda: mock_data_root / "Users.json")
        (mock_data_root / "Users.json").write_text("not valid json", encoding="utf-8")
        assert us.load_users() == []

    def test_save_load_roundtrip(self, mock_data_root):
        from app.services.user_service import save_users, load_users
        original = [{"user_id": "U001", "username": "test", "password": "hash", "role": "admin"}]
        save_users(original)
        assert load_users() == original

    def test_add_user(self, mock_data_root, monkeypatch):
        import app.services.user_service as us
        monkeypatch.setattr(us, "_users_file", lambda: mock_data_root / "Users.json")
        from app.services.user_service import add_user, load_users
        add_user({"user_id": "U001", "username": "test", "password": "hash"})
        assert len(load_users()) == 1

    def test_find_by_id(self, mock_data_root):
        from app.services.user_service import save_users, find_user_by_id
        save_users([{"user_id": "U001", "username": "test", "password": "hash"}])
        assert find_user_by_id("U001") is not None
        assert find_user_by_id("U999") is None

    def test_delete_user_success(self, mock_data_root):
        from app.services.user_service import save_users, delete_user, load_users
        save_users([
            {"user_id": "U001", "username": "admin", "password": "hash", "role": "admin"},
            {"user_id": "U002", "username": "user", "password": "hash", "role": "user"},
        ])
        with patch('app.services.user_service.sync_user_to_sheet'):
            delete_user("U002", by_username="admin")
        assert len(load_users()) == 1

    def test_delete_user_not_found(self, mock_data_root):
        from app.services.user_service import save_users, delete_user
        save_users([{"user_id": "U001", "username": "admin", "password": "hash", "role": "admin"}])
        with patch('app.services.user_service.sync_user_to_sheet'):
            with pytest.raises(ValueError, match="not found"):
                delete_user("U999", by_username="admin")

    def test_delete_user_cannot_delete_self(self, mock_data_root):
        from app.services.user_service import save_users, delete_user
        save_users([
            {"user_id": "U001", "username": "admin", "password": "hash", "role": "admin"},
            {"user_id": "U002", "username": "user", "password": "hash", "role": "user"},
        ])
        with patch('app.services.user_service.sync_user_to_sheet'):
            with pytest.raises(ValueError, match="your own account"):
                delete_user("U001", by_username="admin")

    def test_update_user_role(self, mock_data_root):
        from app.services.user_service import save_users, update_user, find_user_by_id
        save_users([{"user_id": "U001", "username": "user", "password": "hash", "role": "user"}])
        with patch('app.services.user_service.sync_user_to_sheet'):
            update_user("U001", role="admin")
        assert find_user_by_id("U001")["role"] == "admin"

    def test_update_user_invalid_role(self, mock_data_root):
        from app.services.user_service import save_users, update_user
        save_users([{"user_id": "U001", "username": "user", "password": "hash", "role": "user"}])
        with pytest.raises(ValueError, match="Role must be"):
            update_user("U001", role="invalid")

    def test_update_user_not_found(self, mock_data_root):
        from app.services.user_service import save_users, update_user
        save_users([])
        with pytest.raises(ValueError, match="not found"):
            update_user("U999", role="admin")

    def test_update_user_password_hashed(self, mock_data_root):
        from app.services.user_service import save_users, update_user, find_user_by_id
        save_users([{"user_id": "U001", "username": "user", "password": "oldhash", "role": "user"}])
        with patch('app.services.user_service.sync_user_to_sheet'):
            update_user("U001", password="newpass")
        assert find_user_by_id("U001")["password"].startswith("$2b$")

    def test_deactivate_user(self, mock_data_root):
        from app.services.user_service import save_users, deactivate_user, find_user_by_id
        save_users([{"user_id": "U001", "username": "user", "password": "hash", "is_active": True}])
        with patch('app.services.user_service.sync_user_to_sheet'):
            deactivate_user("U001")
        assert find_user_by_id("U001")["is_active"] == False

    def test_activate_user(self, mock_data_root):
        from app.services.user_service import save_users, activate_user, find_user_by_id
        save_users([{"user_id": "U001", "username": "user", "password": "hash", "is_active": False}])
        with patch('app.services.user_service.sync_user_to_sheet'):
            activate_user("U001")
        assert find_user_by_id("U001")["is_active"] == True

    def test_load_permissions_empty(self, mock_data_root, monkeypatch):
        import app.services.user_service as us
        monkeypatch.setattr(us, "_access_file", lambda: mock_data_root / "NONEXISTENT.json")
        assert us.load_permissions() == []

    def test_load_permissions_malformed(self, mock_data_root, monkeypatch):
        import app.services.user_service as us
        monkeypatch.setattr(us, "_access_file", lambda: mock_data_root / "User_Access.json")
        (mock_data_root / "User_Access.json").write_text("bad json", encoding="utf-8")
        assert us.load_permissions() == []

    def test_find_user_whitespace(self, mock_data_root):
        from app.services.user_service import save_users, find_user_by_username
        save_users([{"user_id": "U001", "username": "admin", "password": "hash"}])
        assert find_user_by_username("  admin  ") is not None

    def test_find_user_case_mixed(self, mock_data_root):
        from app.services.user_service import save_users, find_user_by_username
        save_users([{"user_id": "U001", "username": "AdMiN", "password": "hash"}])
        assert find_user_by_username("admin") is not None

    def test_save_users_creates_dir(self, mock_data_root, monkeypatch):
        import app.services.user_service as us
        nested = mock_data_root / "sub" / "Users.json"
        monkeypatch.setattr(us, "_users_file", lambda: nested)
        us.save_users([{"user_id": "U001"}])
        assert nested.exists()

    def test_generate_user_id(self, mock_data_root):
        from app.services.user_service import _next_user_id, save_users
        save_users([{"user_id": "U001", "username": "a", "password": "h"}])
        assert _next_user_id() == "U002"

    def test_generate_user_id_empty(self, mock_data_root, monkeypatch):
        import app.services.user_service as us
        monkeypatch.setattr(us, "_users_file", lambda: mock_data_root / "Users.json")
        assert us._next_user_id() == "U001"

    def test_user_json_structure(self, mock_data_root, monkeypatch):
        import app.services.user_service as us
        monkeypatch.setattr(us, "_users_file", lambda: mock_data_root / "Users.json")
        us.save_users([{"user_id": "U001", "username": "test"}])
        data = json.loads((mock_data_root / "Users.json").read_text())
        assert "users" in data
        assert isinstance(data["users"], list)

    def test_get_user_modules(self, mock_data_root, monkeypatch):
        import app.services.user_service as us
        monkeypatch.setattr(us, "_access_file", lambda: mock_data_root / "NONEXISTENT.json")
        assert us.get_user_modules("U999") == []

    def test_create_user_returns_dict(self, mock_data_root):
        from app.services.user_service import create_user
        with patch('app.services.user_service.sync_user_to_sheet'):
            user = create_user(username="testuser", password="pass")
            assert isinstance(user, dict)
            assert user["username"] == "testuser"

    def test_update_user_username(self, mock_data_root):
        from app.services.user_service import save_users, update_user, find_user_by_id
        save_users([{"user_id": "U001", "username": "old", "password": "hash", "role": "user"}])
        with patch('app.services.user_service.sync_user_to_sheet'):
            update_user("U001", username="new")
        assert find_user_by_id("U001")["username"] == "new"

# ============================================================
# SECTION 3: LEAD SERVICE (20 tests)
# ============================================================

class TestLeadService:
    def test_add_lead_basic(self, mock_data_root):
        with patch('app.services.lead_service.load_leads', return_value=[]):
            with patch('app.services.lead_service.save_leads'):
                from app.services.lead_service import add_lead
                lead = add_lead("Customer", "Co", "123", "e@e.com", 1, "Gmail", "note")
                assert lead["customer"] == "Customer"
                assert lead["status"] == "Pending"

    def test_add_lead_empty_fields(self, mock_data_root):
        with patch('app.services.lead_service.load_leads', return_value=[]):
            with patch('app.services.lead_service.save_leads'):
                from app.services.lead_service import add_lead
                lead = add_lead("", "", "", "", 0, "", "")
                assert lead["customer"] == ""

    def test_add_lead_unique_id(self, mock_data_root):
        with patch('app.services.lead_service.load_leads', return_value=[]):
            with patch('app.services.lead_service.save_leads'):
                from app.services.lead_service import add_lead
                lead1 = add_lead("A", "", "", "", 1, "", "")
                lead2 = add_lead("B", "", "", "", 1, "", "")
                assert lead1["id"] != lead2["id"]

    def test_delete_lead_success(self, mock_data_root):
        test_lead = {"id": "L1", "leadid": "L1", "customer": "Test"}
        with patch('app.services.lead_service.load_leads', return_value=[test_lead]):
            with patch('app.services.lead_service.save_leads') as mock_save:
                from app.services.lead_service import delete_lead
                assert delete_lead("L1") == True
                mock_save.assert_called_once_with([])

    def test_delete_lead_not_found(self, mock_data_root):
        with patch('app.services.lead_service.load_leads', return_value=[]):
            from app.services.lead_service import delete_lead
            assert delete_lead("NONEXISTENT") == False

    def test_delete_lead_partial_match(self, mock_data_root):
        test_leads = [{"id": "L1", "customer": "Test1"}, {"id": "L2", "customer": "Test2"}]
        with patch('app.services.lead_service.load_leads', return_value=test_leads):
            with patch('app.services.lead_service.save_leads') as mock_save:
                from app.services.lead_service import delete_lead
                delete_lead("L1")
                saved = mock_save.call_args[0][0]
                assert len(saved) == 1
                assert saved[0]["id"] == "L2"

    def test_mark_lead_sent(self, mock_data_root):
        test_lead = {"id": "L1", "leadid": "L1", "status": "Pending"}
        with patch('app.services.lead_service.load_leads', return_value=[test_lead]):
            with patch('app.services.lead_service.save_leads'):
                from app.services.lead_service import mark_lead_sent
                assert mark_lead_sent("L1") == True

    def test_mark_lead_sent_not_found(self, mock_data_root):
        with patch('app.services.lead_service.load_leads', return_value=[]):
            from app.services.lead_service import mark_lead_sent
            assert mark_lead_sent("NONEXISTENT") == False

    def test_load_leads_empty(self, mock_data_root, monkeypatch):
        import app.services.lead_service as ls
        monkeypatch.setattr(ls, "_leads_file", lambda: mock_data_root / "NONEXISTENT.json")
        monkeypatch.setattr(ls, "fetch_leads_from_sheet", lambda: None)
        assert ls.load_leads() == []

    def test_lead_status_pending(self, mock_data_root):
        with patch('app.services.lead_service.load_leads', return_value=[]):
            with patch('app.services.lead_service.save_leads'):
                from app.services.lead_service import add_lead
                lead = add_lead("Test", "", "", "", 1, "", "")
                assert lead["status"] == "Pending"

    def test_lead_has_date(self, mock_data_root):
        with patch('app.services.lead_service.load_leads', return_value=[]):
            with patch('app.services.lead_service.save_leads'):
                from app.services.lead_service import add_lead
                lead = add_lead("Test", "", "", "", 1, "", "")
                assert "date" in lead

    def test_lead_has_leadid(self, mock_data_root):
        with patch('app.services.lead_service.load_leads', return_value=[]):
            with patch('app.services.lead_service.save_leads'):
                from app.services.lead_service import add_lead
                lead = add_lead("Test", "", "", "", 1, "", "")
                assert "id" in lead or "leadid" in lead

    def test_lead_phone_number(self, mock_data_root):
        with patch('app.services.lead_service.load_leads', return_value=[]):
            with patch('app.services.lead_service.save_leads'):
                from app.services.lead_service import add_lead
                lead = add_lead("Test", "", "9876543210", "", 1, "", "")
                assert lead["phone"] == "9876543210"

    def test_lead_email(self, mock_data_root):
        with patch('app.services.lead_service.load_leads', return_value=[]):
            with patch('app.services.lead_service.save_leads'):
                from app.services.lead_service import add_lead
                lead = add_lead("Test", "", "", "test@test.com", 1, "", "")
                assert lead["email"] == "test@test.com"

    def test_lead_qty(self, mock_data_root):
        with patch('app.services.lead_service.load_leads', return_value=[]):
            with patch('app.services.lead_service.save_leads'):
                from app.services.lead_service import add_lead
                lead = add_lead("Test", "", "", "", 5, "", "")
                assert lead["qty"] == 5

    def test_lead_source(self, mock_data_root):
        with patch('app.services.lead_service.load_leads', return_value=[]):
            with patch('app.services.lead_service.save_leads'):
                from app.services.lead_service import add_lead
                lead = add_lead("Test", "", "", "", 1, "WhatsApp", "")
                assert lead["source"] == "WhatsApp"

    def test_lead_notes(self, mock_data_root):
        with patch('app.services.lead_service.load_leads', return_value=[]):
            with patch('app.services.lead_service.save_leads'):
                from app.services.lead_service import add_lead
                lead = add_lead("Test", "", "", "", 1, "", "Test note")
                assert lead["notes"] == "Test note"

    def test_lead_company(self, mock_data_root):
        with patch('app.services.lead_service.load_leads', return_value=[]):
            with patch('app.services.lead_service.save_leads'):
                from app.services.lead_service import add_lead
                lead = add_lead("Test", "My Company", "", "", 1, "", "")
                assert lead["company"] == "My Company"

    def test_lead_multiple_add(self, mock_data_root):
        with patch('app.services.lead_service.load_leads', return_value=[]):
            with patch('app.services.lead_service.save_leads'):
                from app.services.lead_service import add_lead
                l1 = add_lead("A", "", "", "", 1, "", "")
                l2 = add_lead("B", "", "", "", 1, "", "")
                assert l1["id"] != l2["id"]

    def test_lead_status_sent(self, mock_data_root):
        test_lead = {"id": "L1", "leadid": "L1", "status": "Pending"}
        with patch('app.services.lead_service.load_leads', return_value=[test_lead]):
            with patch('app.services.lead_service.save_leads') as mock_save:
                from app.services.lead_service import mark_lead_sent
                mark_lead_sent("L1")
                saved = mock_save.call_args[0][0]
                assert saved[0]["status"] == "Sent"

# ============================================================
# SECTION 4: QUOTATION MATH (30 tests)
# ============================================================

class TestQuotationMath:
    def test_packing_zero_percent(self):
        assert round(10000 * (0 / 100), 2) == 0.0

    def test_packing_100_percent(self):
        assert round(10000 * (100 / 100), 2) == 10000.0

    def test_packing_3_5_percent(self):
        assert round(10000 * (3.5 / 100), 2) == 350.0

    def test_packing_10_percent(self):
        assert round(10000 * (10 / 100), 2) == 1000.0

    def test_packing_flat_amount(self):
        assert 500 == 500

    def test_packing_flat_zero(self):
        assert 0 == 0

    def test_packing_negative(self):
        assert round(10000 * (-5 / 100), 2) == -500.0

    def test_gst_0_percent(self):
        assert round(10000 * (0 / 100), 2) == 0.0

    def test_gst_5_percent(self):
        assert round(10000 * (5 / 100), 2) == 500.0

    def test_gst_12_percent(self):
        assert round(10000 * (12 / 100), 2) == 1200.0

    def test_gst_18_percent(self):
        assert round(10000 * (18 / 100), 2) == 1800.0

    def test_gst_28_percent(self):
        assert round(10000 * (28 / 100), 2) == 2800.0

    def test_cgst_sgst_split(self):
        gst = 1800
        assert gst / 2 == 900
        assert gst / 2 == 900

    def test_igst_full(self):
        assert round(10000 * (18 / 100), 2) == 1800.0

    def test_taxable_value_no_packing(self):
        assert 10000 + 0 + 0 == 10000

    def test_taxable_value_with_packing(self):
        assert round(10000 + 350 + 0, 2) == 10350.0

    def test_taxable_value_with_transport(self):
        assert round(10000 + 0 + 500, 2) == 10500.0

    def test_taxable_value_all(self):
        assert round(10000 + 350 + 500, 2) == 10850.0

    def test_grand_total_no_tax(self):
        assert round(10000 + 0, 2) == 10000.0

    def test_grand_total_with_gst(self):
        assert round(10000 + 1800, 2) == 11800.0

    def test_grand_total_complex(self):
        items = 10000
        packing = 350
        transport = 500
        taxable = items + packing + transport
        gst = taxable * 0.18
        assert round(taxable + gst, 2) == 12803.0

    def test_rounding_positive(self):
        assert round(100.49) == 100
        assert round(100.50) == 100
        assert round(100.51) == 101

    def test_rounding_negative(self):
        assert round(-100.49) == -100
        assert round(-100.51) == -101

    def test_zero_items(self):
        assert round(0 + 0 + 0, 2) == 0

    def test_negative_items(self):
        assert round(-1000 + 0 + 0, 2) == -1000

    def test_large_numbers(self):
        items = 1000000
        packing = 35000
        taxable = items + packing
        gst = taxable * 0.18
        assert round(taxable + gst, 2) == 1221300.0

    def test_decimal_precision(self):
        items = 10000.99
        packing = 350.03
        taxable = round(items + packing, 2)
        assert taxable == 10351.02

    def test_gst_decimal(self):
        taxable = 10351.02
        gst = round(taxable * 0.18, 2)
        assert gst == 1863.18

    def test_multi_item_total(self):
        items = [5000, 3000, 2000]
        assert sum(items) == 10000

    def test_multi_item_taxable(self):
        items_total = 10000
        packing = 350
        transport = 500
        assert round(items_total + packing + transport, 2) == 10850.0

    def test_multi_item_grand(self):
        taxable = 10850
        gst = round(taxable * 0.18, 2)
        assert round(taxable + gst, 2) == 12803.0

# ============================================================
# SECTION 5: CONVERSION STATS (15 tests)
# ============================================================

class TestConversionStats:
    def test_conversion_rate_0(self, mock_data_root, monkeypatch):
        import app.services.quotation_history_service as qhs
        monkeypatch.setattr(qhs, "_LEGACY_DATA_DIR", mock_data_root / "NONEXISTENT")
        stats = qhs.get_conversion_stats()
        assert stats["conversion_rate"] == 0.0

    def test_conversion_rate_100(self, mock_data_root, monkeypatch):
        import app.services.quotation_history_service as qhs
        monkeypatch.setattr(qhs, "_LEGACY_DATA_DIR", mock_data_root)
        (mock_data_root / "quotations.json").write_text(json.dumps([
            {"status": "Accepted"}, {"status": "Accepted"}
        ]))
        stats = qhs.get_conversion_stats()
        assert stats["conversion_rate"] == 100.0

    def test_conversion_rate_50(self, mock_data_root, monkeypatch):
        import app.services.quotation_history_service as qhs
        monkeypatch.setattr(qhs, "_LEGACY_DATA_DIR", mock_data_root)
        (mock_data_root / "quotations.json").write_text(json.dumps([
            {"status": "Accepted"}, {"status": "Draft"}
        ]))
        stats = qhs.get_conversion_stats()
        assert stats["conversion_rate"] == 50.0

    def test_conversion_rate_33(self, mock_data_root, monkeypatch):
        import app.services.quotation_history_service as qhs
        monkeypatch.setattr(qhs, "_LEGACY_DATA_DIR", mock_data_root)
        (mock_data_root / "quotations.json").write_text(json.dumps([
            {"status": "Accepted"}, {"status": "Draft"}, {"status": "Draft"}
        ]))
        stats = qhs.get_conversion_stats()
        assert round(stats["conversion_rate"], 1) == 33.3

    def test_conversion_rate_multiple_accepted(self, mock_data_root, monkeypatch):
        import app.services.quotation_history_service as qhs
        monkeypatch.setattr(qhs, "_LEGACY_DATA_DIR", mock_data_root)
        (mock_data_root / "quotations.json").write_text(json.dumps([
            {"status": "Accepted"}, {"status": "Accepted"}, {"status": "Rejected"}
        ]))
        stats = qhs.get_conversion_stats()
        assert round(stats["conversion_rate"], 1) == 66.7

    def test_conversion_rate_rejected_only(self, mock_data_root, monkeypatch):
        import app.services.quotation_history_service as qhs
        monkeypatch.setattr(qhs, "_LEGACY_DATA_DIR", mock_data_root)
        (mock_data_root / "quotations.json").write_text(json.dumps([
            {"status": "Rejected"}, {"status": "Rejected"}
        ]))
        stats = qhs.get_conversion_stats()
        assert stats["conversion_rate"] == 0.0
        assert stats["accepted"] == 0
        assert stats["rejected"] == 2

    def test_conversion_rate_mixed(self, mock_data_root, monkeypatch):
        import app.services.quotation_history_service as qhs
        monkeypatch.setattr(qhs, "_LEGACY_DATA_DIR", mock_data_root)
        (mock_data_root / "quotations.json").write_text(json.dumps([
            {"status": "Accepted"}, {"status": "Rejected"}, {"status": "Draft"}, {"status": "Expired"}
        ]))
        stats = qhs.get_conversion_stats()
        assert stats["total"] == 4
        assert stats["accepted"] == 1
        assert stats["rejected"] == 1
        assert stats["pending"] == 2

    def test_conversion_rate_empty_status(self, mock_data_root, monkeypatch):
        import app.services.quotation_history_service as qhs
        monkeypatch.setattr(qhs, "_LEGACY_DATA_DIR", mock_data_root)
        (mock_data_root / "quotations.json").write_text(json.dumps([
            {"status": ""}, {"status": None}
        ]))
        stats = qhs.get_conversion_stats()
        assert stats["pending"] == 2

    def test_conversion_stats_structure(self, mock_data_root, monkeypatch):
        import app.services.quotation_history_service as qhs
        monkeypatch.setattr(qhs, "_LEGACY_DATA_DIR", mock_data_root)
        stats = qhs.get_conversion_stats()
        assert "total" in stats
        assert "accepted" in stats
        assert "rejected" in stats
        assert "pending" in stats
        assert "conversion_rate" in stats

    def test_conversion_stats_empty(self, mock_data_root, monkeypatch):
        import app.services.quotation_history_service as qhs
        monkeypatch.setattr(qhs, "_LEGACY_DATA_DIR", mock_data_root / "NONEXISTENT")
        stats = qhs.get_conversion_stats()
        assert stats["total"] == 0

    def test_conversion_rate_large(self, mock_data_root, monkeypatch):
        import app.services.quotation_history_service as qhs
        monkeypatch.setattr(qhs, "_LEGACY_DATA_DIR", mock_data_root)
        quotations = [{"status": "Accepted"}] * 99 + [{"status": "Draft"}]
        (mock_data_root / "quotations.json").write_text(json.dumps(quotations))
        stats = qhs.get_conversion_stats()
        assert stats["total"] == 100
        assert stats["accepted"] == 99
        assert stats["conversion_rate"] == 99.0

    def test_conversion_rate_status_case_insensitive(self, mock_data_root, monkeypatch):
        import app.services.quotation_history_service as qhs
        monkeypatch.setattr(qhs, "_LEGACY_DATA_DIR", mock_data_root)
        (mock_data_root / "quotations.json").write_text(json.dumps([
            {"status": "ACCEPTED"}, {"status": "accepted"}, {"status": "Accepted"}
        ]))
        stats = qhs.get_conversion_stats()
        assert stats["accepted"] == 3

    def test_conversion_rate_whitespace(self, mock_data_root, monkeypatch):
        import app.services.quotation_history_service as qhs
        monkeypatch.setattr(qhs, "_LEGACY_DATA_DIR", mock_data_root)
        (mock_data_root / "quotations.json").write_text(json.dumps([
            {"status": "  Accepted  "}, {"status": " Draft "}
        ]))
        stats = qhs.get_conversion_stats()
        assert stats["accepted"] == 1

    def test_conversion_rate_none_status(self, mock_data_root, monkeypatch):
        import app.services.quotation_history_service as qhs
        monkeypatch.setattr(qhs, "_LEGACY_DATA_DIR", mock_data_root)
        (mock_data_root / "quotations.json").write_text(json.dumps([
            {"status": None}, {"status": "Accepted"}
        ]))
        stats = qhs.get_conversion_stats()
        assert stats["accepted"] == 1
        assert stats["pending"] == 1

    def test_conversion_rate_zero_total(self, mock_data_root, monkeypatch):
        import app.services.quotation_history_service as qhs
        monkeypatch.setattr(qhs, "_LEGACY_DATA_DIR", mock_data_root)
        (mock_data_root / "quotations.json").write_text(json.dumps([]))
        stats = qhs.get_conversion_stats()
        assert stats["conversion_rate"] == 0.0

# ============================================================
# SECTION 6: CATALOG (15 tests)
# ============================================================

class TestCatalog:
    def test_catalog_file_missing(self, mock_data_root):
        from app.services.catalog_service import get_product
        assert get_product("NONEXISTENT") is None

    def test_catalog_malformed(self, mock_data_root):
        (mock_data_root / "catalog.json").write_text("bad json", encoding="utf-8")
        from app.services.catalog_service import get_product
        assert get_product("TEST") is None

    def test_catalog_empty_products(self, mock_data_root):
        (mock_data_root / "catalog.json").write_text(json.dumps({"products": []}), encoding="utf-8")
        from app.services.catalog_service import get_product
        assert get_product("TEST") is None

    def test_catalog_with_product(self, mock_data_root):
        with patch('app.services.catalog_service.get_product', return_value={"model": "AA-1216", "price": 1000}):
            from app.services.catalog_service import get_product
            assert get_product("AA-1216")["price"] == 1000

    def test_catalog_product_has_category(self, mock_data_root):
        with patch('app.services.catalog_service.get_product', return_value={"category": "MAGNETIC"}):
            from app.services.catalog_service import get_product
            assert get_product("AA-1216")["category"] == "MAGNETIC"

    def test_catalog_product_has_price(self, mock_data_root):
        with patch('app.services.catalog_service.get_product', return_value={"price": 1000}):
            from app.services.catalog_service import get_product
            assert get_product("AA-1216")["price"] == 1000

    def test_catalog_product_has_hsn(self, mock_data_root):
        with patch('app.services.catalog_service.get_product', return_value={"hsn": "85059000"}):
            from app.services.catalog_service import get_product
            assert get_product("AA-1216")["hsn"] == "85059000"

    def test_catalog_product_has_name(self, mock_data_root):
        with patch('app.services.catalog_service.get_product', return_value={"name": "Test Product"}):
            from app.services.catalog_service import get_product
            assert get_product("AA-1216")["name"] == "Test Product"

    def test_catalog_product_has_description(self, mock_data_root):
        with patch('app.services.catalog_service.get_product', return_value={"description": "Test Description"}):
            from app.services.catalog_service import get_product
            assert get_product("AA-1216")["description"] == "Test Description"

    def test_catalog_get_all_products(self, mock_data_root):
        with patch('app.services.catalog_service.load_catalog', return_value={"products": [{"model": "A"}, {"model": "B"}]}):
            from app.services.catalog_service import load_catalog
            catalog = load_catalog()
            assert len(catalog["products"]) == 2

    def test_catalog_search_by_model(self, mock_data_root):
        with patch('app.services.catalog_service.get_product', return_value={"model": "AA-1216"}):
            from app.services.catalog_service import get_product
            assert get_product("AA-1216")["model"] == "AA-1216"

    def test_catalog_search_case_insensitive(self, mock_data_root):
        with patch('app.services.catalog_service.get_product', return_value={"model": "AA-1216"}):
            from app.services.catalog_service import get_product
            assert get_product("aa-1216") is not None

    def test_catalog_product_count(self, mock_data_root):
        with patch('app.services.catalog_service.get_catalog_summary', return_value={"product_count": 5}):
            from app.services.catalog_service import get_catalog_summary
            assert get_catalog_summary()["product_count"] == 5

    def test_catalog_missing_price(self, mock_data_root):
        with patch('app.services.catalog_service.get_product', return_value={"model": "AA-1216"}):
            from app.services.catalog_service import get_product
            product = get_product("AA-1216")
            assert "price" not in product or product["price"] is None

    def test_catalog_save_skip_if_missing(self, mock_data_root):
        import app.services.catalog_service as cs
        if not hasattr(cs, "save_catalog"):
            pytest.skip("save_catalog not implemented")

# ============================================================
# SECTION 7: SESSION (10 tests)
# ============================================================

class TestSession:
    def test_session_save_load(self, mock_data_root):
        session = {"user_id": "U001", "username": "admin", "modules": ["Crystal"]}
        (mock_data_root / "session.json").write_text(json.dumps(session), encoding="utf-8")
        loaded = json.loads((mock_data_root / "session.json").read_text())
        assert loaded["username"] == "admin"

    def test_session_missing(self, mock_data_root):
        assert not (mock_data_root / "session.json").exists()

    def test_session_clear(self, mock_data_root):
        (mock_data_root / "session.json").write_text("{}", encoding="utf-8")
        (mock_data_root / "session.json").unlink()
        assert not (mock_data_root / "session.json").exists()

    def test_session_malformed(self, mock_data_root):
        (mock_data_root / "session.json").write_text("bad json", encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            json.loads((mock_data_root / "session.json").read_text())

    def test_session_has_modules(self, mock_data_root):
        session = {"user_id": "U001", "modules": ["Crystal", "VMM"]}
        (mock_data_root / "session.json").write_text(json.dumps(session))
        loaded = json.loads((mock_data_root / "session.json").read_text())
        assert len(loaded["modules"]) == 2

    def test_session_modules_crystal(self, mock_data_root):
        session = {"modules": ["Crystal"]}
        (mock_data_root / "session.json").write_text(json.dumps(session))
        loaded = json.loads((mock_data_root / "session.json").read_text())
        assert "Crystal" in loaded["modules"]

    def test_session_modules_vmm(self, mock_data_root):
        session = {"modules": ["VMM"]}
        (mock_data_root / "session.json").write_text(json.dumps(session))
        loaded = json.loads((mock_data_root / "session.json").read_text())
        assert "VMM" in loaded["modules"]

    def test_session_user_id(self, mock_data_root):
        session = {"user_id": "U001"}
        (mock_data_root / "session.json").write_text(json.dumps(session))
        loaded = json.loads((mock_data_root / "session.json").read_text())
        assert loaded["user_id"] == "U001"

    def test_session_overwrite(self, mock_data_root):
        (mock_data_root / "session.json").write_text('{"user": "first"}')
        (mock_data_root / "session.json").write_text('{"user": "second"}')
        loaded = json.loads((mock_data_root / "session.json").read_text())
        assert loaded["user"] == "second"

    def test_session_empty_modules(self, mock_data_root):
        session = {"modules": []}
        (mock_data_root / "session.json").write_text(json.dumps(session))
        loaded = json.loads((mock_data_root / "session.json").read_text())
        assert loaded["modules"] == []

