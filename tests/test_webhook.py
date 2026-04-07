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


def test_get_pending_review_llcs(client):
    """Test GET /api/llc/pending-review returns LLCs awaiting curation."""
    import database

    # Insert test LLCs
    payload = {
        "llcs": [
            {"filing_number": "p1", "business_name": "Pending 1", "filing_date": "2026-04-07",
             "address": "123 Main St", "registered_agent": "Agent 1"},
            {"filing_number": "p2", "business_name": "Pending 2", "filing_date": "2026-04-07",
             "address": "456 Oak Ave", "registered_agent": "Agent 2"}
        ]
    }
    client.post('/api/llc/webhook', data=json.dumps(payload), content_type='application/json')

    response = client.get('/api/llc/pending-review')
    assert response.status_code == 200
    data = response.get_json()
    assert data['count'] >= 2
    assert len(data['llcs']) >= 2

    # Verify all are pending_review status
    for llc in data['llcs']:
        assert llc['status'] == 'pending_review'


def test_get_pending_review_empty(client):
    """Test pending-review returns empty list if no pending LLCs."""
    response = client.get('/api/llc/pending-review')
    assert response.status_code == 200
    data = response.get_json()
    assert data['count'] == 0
    assert data['llcs'] == []


def test_get_pending_review_with_last_hours_filter(client):
    """Test ?last_hours=24 filters to recent LLCs only."""
    # Insert test LLCs via webhook
    payload = {
        "llcs": [
            {"filing_number": "recent", "business_name": "Recent LLC", "filing_date": "2026-04-07",
             "address": "123 Main", "registered_agent": "Agent"}
        ]
    }
    client.post('/api/llc/webhook', data=json.dumps(payload), content_type='application/json')

    # Query with last_hours=24 (should include the just-created LLC)
    response = client.get('/api/llc/pending-review?last_hours=24')
    assert response.status_code == 200
    data = response.get_json()
    assert data['count'] >= 1

    # Query with last_hours=0 (last 0 hours = none)
    response = client.get('/api/llc/pending-review?last_hours=0')
    assert response.status_code == 200
    data = response.get_json()
    # Might be empty or might have LLCs created in the current second, just check it doesn't error
    assert 'count' in data


def test_get_pending_review_with_date_range(client):
    """Test date_from and date_to parameters."""
    from datetime import datetime, timedelta

    # Insert test LLCs
    payload = {
        "llcs": [
            {"filing_number": "date_test_1", "business_name": "Date Test LLC 1", "filing_date": "2026-04-07",
             "address": "123 Main", "registered_agent": "Agent"},
            {"filing_number": "date_test_2", "business_name": "Date Test LLC 2", "filing_date": "2026-04-07",
             "address": "456 Oak", "registered_agent": "Agent"}
        ]
    }
    client.post('/api/llc/webhook', data=json.dumps(payload), content_type='application/json')

    # Use a very wide date range that will definitely include the LLCs
    # (since we just created them, they're in the current datetime range)
    far_past = datetime.utcnow() - timedelta(days=30)
    far_future = datetime.utcnow() + timedelta(days=30)

    # Query with wide date range that includes the insertion time
    response = client.get(f'/api/llc/pending-review?date_from={far_past.isoformat()}&date_to={far_future.isoformat()}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['count'] >= 2, f"Expected at least 2 LLCs, got {data['count']}"

    # Query with date range that excludes today (in the past)
    way_past = (datetime.utcnow() - timedelta(days=2)).isoformat()
    even_more_past = (datetime.utcnow() - timedelta(days=1)).isoformat()

    response = client.get(f'/api/llc/pending-review?date_from={way_past}&date_to={even_more_past}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['count'] == 0, f"Expected 0 LLCs in the past, got {data['count']}"


def test_get_pending_review_invalid_last_hours(client):
    """Test that invalid last_hours parameter returns 400 error."""
    response = client.get('/api/llc/pending-review?last_hours=not_a_number')
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data


def test_get_pending_review_invalid_date_from(client):
    """Test that invalid date_from parameter returns 400 error."""
    response = client.get('/api/llc/pending-review?date_from=not-a-valid-date')
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data


def test_get_pending_review_invalid_date_to(client):
    """Test that invalid date_to parameter returns 400 error."""
    response = client.get('/api/llc/pending-review?date_to=not-a-valid-date')
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data


def test_get_pending_review_ordered_by_creation_date(client):
    """Test that pending-review returns LLCs ordered by creation date ascending (FIFO)."""
    import time
    import database

    # Insert first LLC
    payload1 = {
        "llcs": [
            {"filing_number": "first", "business_name": "First LLC", "filing_date": "2026-04-07",
             "address": "123 Main", "registered_agent": "Agent"}
        ]
    }
    client.post('/api/llc/webhook', data=json.dumps(payload1), content_type='application/json')

    # Small delay to ensure different timestamps
    time.sleep(0.1)

    # Insert second LLC
    payload2 = {
        "llcs": [
            {"filing_number": "second", "business_name": "Second LLC", "filing_date": "2026-04-07",
             "address": "456 Oak", "registered_agent": "Agent"}
        ]
    }
    client.post('/api/llc/webhook', data=json.dumps(payload2), content_type='application/json')

    # Get pending-review LLCs
    response = client.get('/api/llc/pending-review')
    assert response.status_code == 200
    data = response.get_json()

    # Find our two test LLCs
    llcs = data['llcs']
    first_idx = next((i for i, llc in enumerate(llcs) if llc['filing_number'] == 'first'), None)
    second_idx = next((i for i, llc in enumerate(llcs) if llc['filing_number'] == 'second'), None)

    # Both should be present
    assert first_idx is not None
    assert second_idx is not None

    # First should come before second (FIFO order)
    assert first_idx < second_idx
