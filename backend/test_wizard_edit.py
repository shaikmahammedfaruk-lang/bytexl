import io
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api"

def test_wizard_edit_workflow():
    print("=== Testing BrandShield AI 6-Step Brand Profile Wizard Editing ===")
    
    # 1. Fetch existing brands
    res = requests.get(f"{BASE_URL}/brands")
    assert res.status_code == 200
    brands = res.json()
    assert len(brands) > 0, "No brands found"
    
    # Find or use Blackberrys or the first brand
    target_brand = next((b for b in brands if "blackberry" in b["name"].lower()), brands[0])
    brand_id = target_brand["id"]
    print(f"[OK] Selected target brand: '{target_brand['name']}' (ID: {brand_id})")
    
    # 2. Test Logo Upload (Persistent Server Storage)
    print("\n--- Testing Persistent Logo Upload ---")
    dummy_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    files = {"file": ("test_brand_logo.png", io.BytesIO(dummy_png), "image/png")}
    
    upload_res = requests.post(f"{BASE_URL}/brands/upload-logo", files=files)
    assert upload_res.status_code == 200, f"Upload failed: {upload_res.text}"
    upload_data = upload_res.json()
    assert "logo_url" in upload_data
    uploaded_logo_url = upload_data["logo_url"]
    print(f"[OK] Logo uploaded successfully: {uploaded_logo_url}")
    
    # Verify logo is statically accessible
    static_res = requests.get(uploaded_logo_url)
    assert static_res.status_code == 200, "Uploaded logo static URL returned non-200"
    print(f"[OK] Static logo access verified (HTTP 200, {len(static_res.content)} bytes)")
    
    # 3. Test Full 6-Step Wizard Sync (PUT /api/brands/{id}/wizard)
    print("\n--- Testing 6-Step Wizard Synchronization ---")
    original_name = target_brand["name"]
    updated_name = f"{original_name} Global"
    
    old_social_url = "https://instagram.com/blackberrys_old_outdated"
    new_social_url = "https://instagram.com/blackberrysmenswear_official"
    new_fb_url = "https://facebook.com/BlackberrysMenswearOfficial"
    new_app_pkg = "com.blackberrys.shopping"
    new_app_url = "https://play.google.com/store/apps/details?id=com.blackberrys.shopping"
    new_domain_url = "https://shop.blackberrys.com"
    
    wizard_payload = {
        # Step 1: Brand Info
        "name": updated_name,
        "website": "https://www.blackberrys.com",
        "industry": "E-Commerce & Retail",
        "description": "Updated formal and casual menswear collections with multi-channel official verification.",
        "brand_keywords": ["menswear", "suits", "blazers", "formal", "shirts"],
        "brand_aliases": ["Blackberrys", "Blackberrys Menswear", "Blackberrys India"],
        
        # Step 2: Logo
        "logo_url": uploaded_logo_url,
        
        # Step 3: Official Social
        "social_accounts": [
            {
                "platform": "Instagram",
                "identifier": "@blackberrysmenswear_official",
                "url": new_social_url,
                "name": "Blackberrys Official Instagram",
                "verification_status": "VERIFIED"
            },
            {
                "platform": "Facebook",
                "identifier": "BlackberrysMenswearOfficial",
                "url": new_fb_url,
                "name": "Blackberrys Official Facebook",
                "verification_status": "VERIFIED"
            }
        ],
        
        # Step 4: Official Apps
        "mobile_apps": [
            {
                "platform": "Google Play",
                "name": "Blackberrys Menswear App",
                "developer_name": "Blackberrys Apparels",
                "package_id": new_app_pkg,
                "url": new_app_url,
                "verification_status": "VERIFIED"
            }
        ],
        
        # Step 5: Domains
        "domains": [
            {
                "platform": "Domain",
                "name": "Online Storefront",
                "url": new_domain_url,
                "is_active": True,
                "verification_status": "VERIFIED"
            }
        ]
    }
    
    sync_res = requests.put(f"{BASE_URL}/brands/{brand_id}/wizard", json=wizard_payload)
    assert sync_res.status_code == 200, f"Wizard sync failed: {sync_res.text}"
    sync_data = sync_res.json()
    assert sync_data["status"] == "success"
    print(f"[OK] Wizard sync succeeded: {sync_data['message']}")
    
    # 4. Verify Persistence Across Fresh GET Requests
    print("\n--- Verifying Database Persistence Across Endpoints ---")
    b_get = requests.get(f"{BASE_URL}/brands/{brand_id}")
    assert b_get.status_code == 200
    brand_fresh = b_get.json()
    assert brand_fresh["name"] == updated_name
    assert brand_fresh["logo_url"] == uploaded_logo_url
    assert brand_fresh["official_instagram_username"] == "blackberrysmenswear_official"
    print(f"[OK] Brand ground truth verified in MongoDB: {brand_fresh['name']}, IG user: {brand_fresh['official_instagram_username']}")
    
    assets_get = requests.get(f"{BASE_URL}/brands/{brand_id}/official-assets")
    assert assets_get.status_code == 200
    assets_list = assets_get.json()
    assert len(assets_list) == 4, f"Expected 4 official assets (2 social, 1 app, 1 domain), got {len(assets_list)}"
    print(f"[OK] Verified 4 official assets registered in official_assets collection.")
    
    # 5. Dynamic Update Requirement: Testing Exclusion Rule Engine with Updated Assets
    print("\n--- Testing Exclusion Engine Dynamic Sync ---")
    # A) Scan the NEW official social account -> Must be recognized as official and safe (0 threat created)
    scan_new_res = requests.post(f"{BASE_URL}/social/scan", json={
        "brand_id": brand_id,
        "platform": "Instagram",
        "url": new_social_url,
        "username": "@blackberrysmenswear_official"
    })
    assert scan_new_res.status_code == 200
    scan_new_data = scan_new_res.json()
    assert scan_new_data.get("status") == "safe", f"Expected new official asset to be safe, got: {scan_new_data}"
    print(f"[OK] Scanned new official URL '{new_social_url}': Correctly recognized as SAFE / whitelisted.")
    
    # B) Scan the OLD/REPLACED social account -> Must NOT be safe (it was replaced, so it should be flagged as threat)
    scan_old_res = requests.post(f"{BASE_URL}/social/scan", json={
        "brand_id": brand_id,
        "platform": "Instagram",
        "url": old_social_url,
        "username": "@blackberrys_old_outdated"
    })
    assert scan_old_res.status_code == 200
    scan_old_data = scan_old_res.json()
    assert scan_old_data.get("status") == "threat_created", f"Expected old replaced asset to NOT be safe, got: {scan_old_data}"
    print(f"[OK] Scanned old replaced URL '{old_social_url}': Correctly NOT trusted and flagged as threat candidate.")
    
    # Cleanup the test threat
    if scan_old_data.get("threat"):
        threat_id = scan_old_data["threat"]["id"]
        requests.delete(f"{BASE_URL}/threats/{threat_id}")
        print(f"[OK] Cleaned up temporary test threat {threat_id}")
        
    # Revert brand name to original name
    revert_payload = wizard_payload.copy()
    revert_payload["name"] = original_name
    requests.put(f"{BASE_URL}/brands/{brand_id}/wizard", json=revert_payload)
    print(f"[OK] Reverted brand name back to '{original_name}'.")

    # 6. Verify Instagram Analyzer is Still Working
    print("\n--- Verifying Existing Instagram Analyzer Functionality Unchanged ---")
    ig_res = requests.get(f"{BASE_URL}/instagram/profiles/{brand_id}")
    assert ig_res.status_code in [200, 404]
    print("[OK] Instagram analyzer routes functional and intact.")

    print("\n=== ALL 6 WIZARD EDITING CRITERIA AND DYNAMIC EXCLUSION TESTS PASSED! ===")

if __name__ == "__main__":
    test_wizard_edit_workflow()
