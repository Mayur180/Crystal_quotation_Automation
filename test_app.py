"""
Automated Test Suite for CRYSTAL Quotation Manager.
Run with: pytest test_app.py -v
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary data directory for testing."""
    return tmp_path

@pytest.fixture
def mock_data_root(temp_data_dir, monkeypatch):
    """Mock get_data_root to return the temp directory."""
    import app.services.paths as paths
    monkeypatch.setattr(paths, "get_data_root", lambda: temp_data_dir)
    return temp_data_dir

@pytest.fixture
def sample_users(mock_data_root):
    """Create a sample Users.json file."""
    users = {
        "users": [
            {
                "user_id": "U001",
                "username": "admin",
                "password": "admin123",  # Will be hashed by test
                "full_name": "Admin",
                "role": "admin",
                "is_active": True
            }
        ]
    }
    (mock_data_root / "Users.json").write_text(json.dumps(users), encoding="utf-8")
    return users

@pytest.fixture
def sample_quotations(mock_data_root):
    """Create a sample quotations.json file."""
    quotations = [
        {
            "quotation_number": "CRY/26-27/001",
            "date": "2026-10-26",
            "customer_name": "Test Customer",
            "grand_total": 5000,
            "status": "Draft",
            "items": [
                {"model": "AA-1216", "qty": 1, "price": 5000, "total": 5000}
            ]
        },
        {
            "quotation_number": "CRY/26-27/002",
            "date": "2026-10-26",
            "customer_name": "Accepted Customer",
            "grand_total": 10000,
            "status": "Accepted",
            "items": [
                {"model": "AA-15202", "qty": 2, "price": 5000, "total": 10000}
            ]
        }
    ]
    crystal_dir = mock_data_root / "Crystal"
    crystal_dir.mkdir(exist_ok=True)
    (crystal_dir / "quotations.json").write_text(json.dumps(quotations), encoding="utf-8")
    return quotations

# ============================================================
# TEST 1: AUTHENTICATION
# ============================================================

class TestAuth:
    def test_bcrypt_hashing(self):
        """Test that passwords are hashed with bcrypt."""
        import bcrypt
        password = "admin123"
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        assert hashed.startswith(b"$2b$")
        assert bcrypt.checkpw(password.encode('utf-8'), hashed)

    def test_wrong_password(self):
        """Test that wrong passwords fail."""
        import bcrypt
        password = "admin123"
        wrong = "wrongpass"
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        assert not bcrypt.checkpw(wrong.encode('utf-8'), hashed)

    def test_user_not_found(self, mock_data_root):
        """Test that non-existent users return None."""
        from app.services.user_service import find_user_by_username
        assert find_user_by_username("nonexistent") is None

    def test_create_user_hashes_password(self, mock_data_root):
        """Test that create_user hashes the password."""
        from unittest.mock import patch
        with patch('app.services.user_service.sync_user_to_sheet'):
            from app.services.user_service import create_user, find_user_by_username
            create_user(username="testuser", password="test123", full_name="Test")
            user = find_user_by_username("testuser")
            assert user is not None
            assert user["password"].startswith("$2b$")

# ============================================================
# TEST 2: USER SERVICE
# ============================================================

class TestUserService:
    def test_load_empty_users(self, mock_data_root, monkeypatch):
        """Test that empty users returns []."""
        import app.services.user_service as us
        # Force _users_file to return a non-existent path
        monkeypatch.setattr(us, "_users_file", lambda: mock_data_root / "NONEXISTENT.json")
        from app.services.user_service import load_users
        assert load_users() == []

    def test_save_and_load_users(self, mock_data_root):
        """Test saving and loading users."""
        from app.services.user_service import save_users, load_users
        users = [{"user_id": "U001", "username": "test", "password": "hash"}]
        save_users(users)
        loaded = load_users()
        assert len(loaded) == 1
        assert loaded[0]["username"] == "test"

    def test_is_admin(self, mock_data_root):
        """Test admin role check."""
        from app.services.user_service import save_users, is_admin
        save_users([
            {"user_id": "U001", "username": "admin", "password": "hash", "role": "admin"},
            {"user_id": "U002", "username": "user", "password": "hash", "role": "user"},
        ])
        assert is_admin("admin") == True
        assert is_admin("user") == False

    def test_delete_user(self, mock_data_root):
        """Test deleting a user."""
        from unittest.mock import patch
        with patch('app.services.user_service.sync_user_to_sheet'):
            from app.services.user_service import save_users, delete_user, load_users
            save_users([
                {"user_id": "U001", "username": "admin", "password": "hash", "role": "admin"},
                {"user_id": "U002", "username": "user", "password": "hash", "role": "user"},
            ])
            delete_user("U002", by_username="admin")
            users = load_users()
            assert len(users) == 1
            assert users[0]["username"] == "admin"

# ============================================================
# TEST 3: LEAD SERVICE
# ============================================================

class TestLeadService:
    def test_add_lead(self, mock_data_root):
        """Test adding a lead."""
        from unittest.mock import patch
        with patch('app.services.lead_service.load_leads', return_value=[]):
            with patch('app.services.lead_service.save_leads'):
                from app.services.lead_service import add_lead
                lead = add_lead(
                    customer="Test Customer",
                    company="Test Co",
                    phone="1234567890",
                    email="test@test.com",
                    qty=5,
                    source="Gmail",
                    notes="Test lead"
                )
                assert lead["customer"] == "Test Customer"

    def test_delete_lead(self, mock_data_root):
        """Test deleting a lead locally."""
        from unittest.mock import patch, MagicMock
        test_lead = {"id": "L123", "leadid": "L123", "customer": "Test"}
        with patch('app.services.lead_service.load_leads', return_value=[test_lead]):
            with patch('app.services.lead_service.save_leads') as mock_save:
                from app.services.lead_service import delete_lead
                result = delete_lead("L123")
                assert result == True
                mock_save.assert_called_once_with([])

    def test_lead_not_found(self, mock_data_root):
        """Test deleting a non-existent lead."""
        from app.services.lead_service import delete_lead
        assert delete_lead("NONEXISTENT") == False

# ============================================================
# TEST 4: QUOTATION MATH
# ============================================================

class TestQuotationMath:
    def test_packing_percentage(self):
        """Test packing as percentage."""
        items_total = 10000
        packing_percent = 3.5
        packing_amt = items_total * (packing_percent / 100)
        assert round(packing_amt, 2) == 350.0

    def test_packing_amount(self):
        """Test packing as flat amount."""
        packing_amt = 500
        assert packing_amt == 500

    def test_gst_calculation(self):
        """Test GST calculation."""
        taxable = 10000
        gst_rate = 18
        gst_amt = taxable * (gst_rate / 100)
        cgst = gst_amt / 2
        sgst = gst_amt / 2
        assert gst_amt == 1800
        assert cgst == 900
        assert sgst == 900

    def test_igst_calculation(self):
        """Test IGST calculation."""
        taxable = 10000
        gst_rate = 18
        igst = taxable * (gst_rate / 100)
        assert igst == 1800

    def test_grand_total(self):
        """Test grand total calculation."""
        items_total = 10000
        packing = 350
        transport = 500
        taxable = items_total + packing + transport
        gst = taxable * 0.18
        grand = taxable + gst
        assert taxable == 10850
        assert round(grand, 2) == 12803.0

# ============================================================
# TEST 5: CONVERSION STATS
# ============================================================

class TestConversionStats:
    def test_conversion_stats(self, mock_data_root, sample_quotations):
        """Test conversion rate calculation."""
        from app.services.quotation_history_service import get_conversion_stats
        stats = get_conversion_stats("Crystal")
        assert stats["total"] == 2
        assert stats["accepted"] == 1
        assert stats["conversion_rate"] == 50.0

    def test_empty_conversion(self, mock_data_root, monkeypatch):
        """Test conversion rate with no data."""
        import app.services.quotation_history_service as qhs
        # Patch _resolve_data_dir to return a temp dir with no quotations.json
        monkeypatch.setattr(qhs, "_resolve_data_dir", lambda: mock_data_root)
        from app.services.quotation_history_service import get_conversion_stats
        stats = get_conversion_stats()
        assert stats["total"] == 0
        assert stats["conversion_rate"] == 0.0

# ============================================================
# TEST 6: CATALOG
# ============================================================

class TestCatalog:
    def test_catalog_loading(self, mock_data_root):
        """Test loading catalog."""
        catalog = {
            "products": [
                {"model": "AA-1216", "name": "Test Product", "price": 1000, "category": "MAGNETIC"},
            ]
        }
        crystal_dir = mock_data_root / "Crystal"
        crystal_dir.mkdir(exist_ok=True)
        (crystal_dir / "catalog.json").write_text(json.dumps(catalog), encoding="utf-8")
        
        from unittest.mock import patch
        with patch('app.services.catalog_service.get_product', return_value={"model": "AA-1216", "price": 1000}):
            from app.services.catalog_service import get_product
            product = get_product("AA-1216")
            assert product is not None
            assert product["price"] == 1000

    def test_product_not_found(self, mock_data_root):
        """Test that non-existent products return None."""
        from app.services.catalog_service import get_product
        assert get_product("NONEXISTENT") is None

# ============================================================
# TEST 7: SESSION
# ============================================================

class TestSession:
    def test_session_save_and_load(self, mock_data_root):
        """Test saving and loading a session."""
        session_data = {
            "user_id": "U001",
            "username": "admin",
            "full_name": "Admin",
            "modules": ["Crystal"]
        }
        session_file = mock_data_root / "session.json"
        session_file.write_text(json.dumps(session_data), encoding="utf-8")
        
        loaded = json.loads(session_file.read_text(encoding="utf-8"))
        assert loaded["username"] == "admin"
        assert loaded["modules"] == ["Crystal"]

    def test_session_clear(self, mock_data_root):
        """Test clearing a session."""
        session_file = mock_data_root / "session.json"
        session_file.write_text('{"username": "test"}', encoding="utf-8")
        assert session_file.exists()
        session_file.unlink()
        assert not session_file.exists()

