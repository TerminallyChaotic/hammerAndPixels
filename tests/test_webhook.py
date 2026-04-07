import pytest
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'llcScraper'))


def test_webhook_receives_llcs(client):
    """Test POST /api/llc/webhook stores LLCs with pending_review status."""
    payload = {
        "llcs": [
            {
                "filing_number": "12345",
                "business_name": "Test LLC",
                "filing_date": "2026-04-07",
                "address": "123 Main St, Hartford, CT",
                "registered_agent": "John Doe"
            }
        ]
    }

    response = client.post(
        '/api/llc/webhook',
        data=json.dumps(payload),
        content_type='application/json'
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['count'] == 1


def test_webhook_stores_with_pending_review_status(client):
    """Test that webhook-received LLCs have status='pending_review'."""
    import database

    payload = {
        "llcs": [
            {
                "filing_number": "54321",
                "business_name": "Another LLC",
                "filing_date": "2026-04-06",
                "address": "456 Oak Ave, Farmington, CT",
                "registered_agent": "Jane Smith"
            }
        ]
    }

    client.post('/api/llc/webhook', data=json.dumps(payload), content_type='application/json')

    llc = database.get_llc_by_filing_number("54321")
    assert llc is not None
    assert llc['status'] == 'pending_review'
    assert llc['openclaw_reviewed'] == 0  # SQLite uses 0/1 for booleans


def test_webhook_returns_error_on_invalid_payload(client):
    """Test that webhook rejects invalid payloads."""
    response = client.post(
        '/api/llc/webhook',
        data=json.dumps({"invalid": "data"}),
        content_type='application/json'
    )

    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data


def test_webhook_returns_error_on_empty_llcs_list(client):
    """Test that webhook rejects empty llcs list."""
    response = client.post(
        '/api/llc/webhook',
        data=json.dumps({"llcs": []}),
        content_type='application/json'
    )

    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data


def test_webhook_skips_llc_with_missing_fields(client):
    """Test that webhook skips LLCs with missing required fields."""
    import database

    payload = {
        "llcs": [
            {
                "filing_number": "99999",
                "business_name": "Missing Address LLC",
                # Missing address, registered_agent
                "filing_date": "2026-04-06"
            }
        ]
    }

    response = client.post(
        '/api/llc/webhook',
        data=json.dumps(payload),
        content_type='application/json'
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['count'] == 0  # Should skip the incomplete LLC

    # Verify it wasn't saved
    llc = database.get_llc_by_filing_number("99999")
    assert llc is None


def test_webhook_stores_multiple_llcs(client):
    """Test that webhook handles multiple LLCs in one request."""
    import database

    payload = {
        "llcs": [
            {
                "filing_number": "11111",
                "business_name": "First LLC",
                "filing_date": "2026-04-07",
                "address": "111 First St, Hartford, CT",
                "registered_agent": "Agent One"
            },
            {
                "filing_number": "22222",
                "business_name": "Second LLC",
                "filing_date": "2026-04-07",
                "address": "222 Second Ave, Hartford, CT",
                "registered_agent": "Agent Two"
            }
        ]
    }

    response = client.post(
        '/api/llc/webhook',
        data=json.dumps(payload),
        content_type='application/json'
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['count'] == 2

    # Verify both were saved
    llc1 = database.get_llc_by_filing_number("11111")
    llc2 = database.get_llc_by_filing_number("22222")
    assert llc1 is not None
    assert llc2 is not None
    assert llc1['status'] == 'pending_review'
    assert llc2['status'] == 'pending_review'


def test_webhook_stores_optional_fields(client):
    """Test that webhook stores optional fields like email and naics_code."""
    import database

    payload = {
        "llcs": [
            {
                "filing_number": "77777",
                "business_name": "Full Info LLC",
                "filing_date": "2026-04-07",
                "address": "777 Full St, Hartford, CT",
                "registered_agent": "Full Agent",
                "email_address": "info@fullllc.com",
                "naics_code": "541110"
            }
        ]
    }

    response = client.post(
        '/api/llc/webhook',
        data=json.dumps(payload),
        content_type='application/json'
    )

    assert response.status_code == 200

    llc = database.get_llc_by_filing_number("77777")
    assert llc is not None
    assert llc['email_address'] == "info@fullllc.com"
    assert llc['enrichment_notes'] == "541110"  # naics_code goes to enrichment_notes


def test_webhook_with_invalid_json(client):
    """Test that webhook handles invalid JSON gracefully."""
    response = client.post(
        '/api/llc/webhook',
        data='not valid json',
        content_type='application/json'
    )

    assert response.status_code == 500
    data = response.get_json()
    assert 'error' in data
