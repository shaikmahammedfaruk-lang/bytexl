import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000/api"

def test_crud():
    print("=== Testing BrandShield AI CRUD Operations ===")
    
    # 0. Health / Brands check
    res = requests.get(f"{BASE_URL}/brands")
    assert res.status_code == 200, f"Failed to get brands: {res.text}"
    existing_brands = res.json()
    print(f"[OK] Fetched {len(existing_brands)} existing brands.")
    
    # 1. Brand Profile CRUD
    print("\n--- 1. Testing Brand Profile CRUD ---")
    brand_payload = {
        "name": "Test Brand Shield Corp",
        "category": "Technology & Cybersecurity",
        "description": "Enterprise test brand for CRUD automation.",
        "official_website": "https://testbrandshield.com",
        "logo_url": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=100",
        "keywords": ["test", "brandshield", "security"]
    }
    
    # Pre-clean any test brands from previous runs
    for b in existing_brands:
        if b["name"] in [brand_payload["name"], "Test Brand Shield Corp Updated"]:
            requests.delete(f"{BASE_URL}/brands/{b['id']}")

    # Create brand
    res = requests.post(f"{BASE_URL}/brands", json=brand_payload)
    assert res.status_code in [200, 201], f"Failed to create brand: {res.text}"
    brand = res.json()
    brand_id = brand["id"]
    print(f"[OK] Created Brand: {brand['name']} (ID: {brand_id})")
    
    # Read brand
    res = requests.get(f"{BASE_URL}/brands/{brand_id}")
    assert res.status_code == 200, f"Failed to read brand: {res.text}"
    assert res.json()["name"] == brand_payload["name"]
    print(f"[OK] Read Brand: {res.json()['name']}")
    
    # Update brand
    update_payload = {
        "name": "Test Brand Shield Corp Updated",
        "description": "Updated brand description for testing."
    }
    res = requests.put(f"{BASE_URL}/brands/{brand_id}", json=update_payload)
    assert res.status_code == 200, f"Failed to update brand: {res.text}"
    assert res.json()["name"] == "Test Brand Shield Corp Updated"
    print(f"[OK] Updated Brand: {res.json()['name']}")
    
    # Add Official Asset
    asset_payload = {
        "brand_id": brand_id,
        "name": "Official Instagram Handle",
        "asset_type": "social",
        "platform": "Instagram",
        "identifier": "testbrandshield",
        "url": "https://instagram.com/testbrandshield"
    }
    res = requests.post(f"{BASE_URL}/brands/{brand_id}/official-assets", json=asset_payload)
    assert res.status_code in [200, 201], f"Failed to add official asset: {res.text}"
    asset = res.json()
    asset_id = asset["id"]
    print(f"[OK] Added Official Asset: {asset['identifier']} (Asset ID: {asset_id})")
    
    # Update Official Asset
    asset_update = {
        "identifier": "testbrandshield_official",
        "url": "https://instagram.com/testbrandshield_official"
    }
    res = requests.put(f"{BASE_URL}/brands/{brand_id}/official-assets/{asset_id}", json=asset_update)
    assert res.status_code == 200, f"Failed to update official asset: {res.text}"
    updated_asset = res.json()
    assert updated_asset["identifier"] == "testbrandshield_official"
    print(f"[OK] Updated Official Asset: {updated_asset['identifier']}")
    
    # Delete Official Asset
    res = requests.delete(f"{BASE_URL}/brands/{brand_id}/official-assets/{asset_id}")
    assert res.status_code == 200, f"Failed to delete official asset: {res.text}"
    print(f"[OK] Deleted Official Asset: {asset_id}")
    
    # 2. Social Monitoring CRUD
    print("\n--- 2. Testing Social Monitoring CRUD ---")
    social_scan_payload = {
        "brand_id": brand_id,
        "platform": "instagram",
        "url": "https://instagram.com/fake_testbrandshield_support",
        "username": "fake_testbrandshield_support"
    }
    res = requests.post(f"{BASE_URL}/social/scan", json=social_scan_payload)
    assert res.status_code == 200, f"Failed to scan social link: {res.text}"
    scan_data = res.json()
    social_threat = scan_data.get("threat") or scan_data
    social_threat_id = social_threat["id"]
    print(f"[OK] Created Social Threat: {social_threat['account_or_app_name']} (ID: {social_threat_id})")
    
    # Read social threats
    res = requests.get(f"{BASE_URL}/social/threats?brand_id={brand_id}")
    assert res.status_code == 200
    assert any(t["id"] == social_threat_id for t in res.json())
    print(f"[OK] Read Social Threats list, found ID {social_threat_id}")
    
    # Update social threat
    social_update_payload = {
        "status": "UNDER_INVESTIGATION",
        "analyst_assigned": "Senior Investigator",
        "note": "Investigating unauthorized support account."
    }
    res = requests.put(f"{BASE_URL}/social/threats/{social_threat_id}", json=social_update_payload)
    assert res.status_code == 200, f"Failed to update social threat: {res.text}"
    assert res.json()["status"] == "UNDER_INVESTIGATION"
    print(f"[OK] Updated Social Threat Status: {res.json()['status']}")
    
    # Delete social threat
    res = requests.delete(f"{BASE_URL}/social/threats/{social_threat_id}")
    assert res.status_code == 200, f"Failed to delete social threat: {res.text}"
    print(f"[OK] Deleted Social Threat: {social_threat_id}")
    
    # 3. App Monitoring CRUD & Duplicate Detection
    print("\n--- 3. Testing App Monitoring CRUD & Duplicate Detection ---")
    app_scan_payload = {
        "brand_id": brand_id,
        "store": "google_play",
        "package_id": "com.fake.testbrandshield.wallet",
        "app_name": "Test BrandShield Fake Wallet",
        "developer_name": "Rogue Developer Ltd",
        "url": "https://play.google.com/store/apps/details?id=com.fake.testbrandshield.wallet"
    }
    res = requests.post(f"{BASE_URL}/apps/scan", json=app_scan_payload)
    assert res.status_code == 200, f"Failed to scan app: {res.text}"
    app_scan_data = res.json()
    app_threat = app_scan_data.get("threat") or app_scan_data
    app_threat_id = app_threat["id"]
    print(f"[OK] Created App Threat: {app_threat['account_or_app_name']} (ID: {app_threat_id})")
    
    # Test duplicate detection: scanning same package ID should return existing record without creating duplicate
    res_dup = requests.post(f"{BASE_URL}/apps/scan", json=app_scan_payload)
    assert res_dup.status_code == 200
    dup_threat = res_dup.json().get("threat") or res_dup.json()
    assert dup_threat["id"] == app_threat_id, "Duplicate detection failed: created a duplicate instead of reusing existing record"
    print(f"[OK] Duplicate check passed: reused existing record ID {app_threat_id}")
    
    # Read app threats
    res = requests.get(f"{BASE_URL}/apps/threats?brand_id={brand_id}")
    assert res.status_code == 200
    assert any(t["id"] == app_threat_id for t in res.json())
    print(f"[OK] Read App Threats list, found ID {app_threat_id}")
    
    # Update app threat
    app_update_payload = {
        "status": "REVIEWED",
        "analyst_assigned": "Mobile Security Lead",
        "note": "Developer mismatch confirmed. Rogue entity."
    }
    res = requests.put(f"{BASE_URL}/apps/threats/{app_threat_id}", json=app_update_payload)
    assert res.status_code == 200, f"Failed to update app threat: {res.text}"
    assert res.json()["status"] == "REVIEWED"
    print(f"[OK] Updated App Threat Status: {res.json()['status']}")
    
    # Delete app threat
    res = requests.delete(f"{BASE_URL}/apps/threats/{app_threat_id}")
    assert res.status_code == 200, f"Failed to delete app threat: {res.text}"
    print(f"[OK] Deleted App Threat: {app_threat_id}")
    
    # 4. Threat Center Checkbox-Based Bulk Delete
    print("\n--- 4. Testing Threat Center Checkbox-Based Bulk Delete ---")
    # Create two threats for bulk deletion testing
    t1_res = requests.post(f"{BASE_URL}/social/scan", json={
        "brand_id": brand_id,
        "platform": "facebook",
        "url": "https://facebook.com/fake_brand_1",
        "username": "fake_brand_1"
    })
    t2_res = requests.post(f"{BASE_URL}/social/scan", json={
        "brand_id": brand_id,
        "platform": "x",
        "url": "https://x.com/fake_brand_2",
        "username": "fake_brand_2"
    })
    assert t1_res.status_code == 200 and t2_res.status_code == 200
    t1_id = (t1_res.json().get("threat") or t1_res.json())["id"]
    t2_id = (t2_res.json().get("threat") or t2_res.json())["id"]
    print(f"[OK] Created 2 threats for bulk delete: {t1_id}, {t2_id}")
    
    # Bulk delete
    bulk_res = requests.post(f"{BASE_URL}/threats/bulk-delete", json={"ids": [t1_id, t2_id]})
    assert bulk_res.status_code == 200, f"Failed bulk delete: {bulk_res.text}"
    assert bulk_res.json()["deleted_count"] == 2
    print(f"[OK] Bulk deleted {bulk_res.json()['deleted_count']} threats via /threats/bulk-delete")
    
    # Verify threats are gone
    check_t1 = requests.get(f"{BASE_URL}/threats/{t1_id}")
    assert check_t1.status_code == 404, "Threat t1 should be deleted"
    check_t2 = requests.get(f"{BASE_URL}/threats/{t2_id}")
    assert check_t2.status_code == 404, "Threat t2 should be deleted"
    print(f"[OK] Verified threats {t1_id} and {t2_id} no longer exist in database")
    
    # 5. Brand Cascade Deletion Test
    print("\n--- 5. Testing Brand Cascade Deletion ---")
    # Add a threat under the brand first
    t3_res = requests.post(f"{BASE_URL}/social/scan", json={
        "brand_id": brand_id,
        "platform": "tiktok",
        "url": "https://tiktok.com/@fake_brand_3",
        "username": "fake_brand_3"
    })
    t3_id = (t3_res.json().get("threat") or t3_res.json())["id"]
    
    # Delete the brand
    del_brand_res = requests.delete(f"{BASE_URL}/brands/{brand_id}")
    assert del_brand_res.status_code == 200, f"Failed to delete brand: {del_brand_res.text}"
    print(f"[OK] Brand {brand_id} deleted successfully")
    
    # Verify cascade deleted threat
    check_t3 = requests.get(f"{BASE_URL}/threats/{t3_id}")
    assert check_t3.status_code == 404, "Dependent threat should have been deleted with brand"
    print(f"[OK] Verified dependent threat {t3_id} was safely cascade-deleted with brand")
    
    print("\n=== ALL CRUD OPERATIONS AND BULK DELETE TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    test_crud()
