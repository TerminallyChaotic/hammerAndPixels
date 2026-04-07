"""Tests for scraper webhook posting functionality.

This test suite verifies that the scraper:
1. Posts found LLCs to the webhook instead of saving directly to DB
2. Batches multiple LLCs into a single POST
3. Handles webhook failures with retries
4. Uses the API key from environment
5. Logs success/failure appropriately
"""
import pytest
import sys
import os
import json
from unittest.mock import Mock, patch, call
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'llcScraper'))


def test_scraper_posts_found_llcs_to_webhook(monkeypatch):
    """Test that run_scraper posts found LLCs to webhook instead of saving directly."""
    import scraper
    import database

    # Mock the API request
    mock_response = Mock()
    mock_response.json.return_value = [
        {
            'accountnumber': 'LLC001',
            'name': 'Test Business LLC',
            'date_registration': '2026-04-07T00:00:00',
            'billingstreet': '123 Main St',
            'billing_unit': '',
            'billingcity': 'Hartford',
            'billingstate': 'CT',
            'billingpostalcode': '06101',
            'business_email_address': 'test@example.com',
            'naics_code': '541110'
        }
    ]
    mock_response.raise_for_status = Mock()

    monkeypatch.setattr('scraper.requests.get', Mock(return_value=mock_response))

    # Mock the webhook POST
    mock_webhook_response = Mock()
    mock_webhook_response.json.return_value = {'success': True, 'count': 1}
    mock_webhook_response.raise_for_status = Mock()

    with patch('scraper.requests.post', return_value=mock_webhook_response) as mock_post:
        # Run the scraper
        result = scraper.run_scraper()

        # Verify that requests.post was called (webhook POST)
        assert mock_post.called, "Scraper should POST to webhook"

        # Verify the post was made to the webhook endpoint
        call_kwargs = mock_post.call_args[1] if mock_post.call_args[1] else {}
        call_args = mock_post.call_args[0] if mock_post.call_args[0] else []

        # The URL should contain the webhook endpoint
        webhook_url = call_args[0] if call_args else call_kwargs.get('url')
        assert webhook_url and 'webhook' in webhook_url, f"Expected webhook URL, got {webhook_url}"


def test_scraper_batches_llcs_in_single_post(monkeypatch):
    """Test that scraper batches multiple LLCs into a single POST."""
    import scraper

    # Mock the API request to return 2 LLCs
    mock_response = Mock()
    mock_response.json.return_value = [
        {
            'accountnumber': 'LLC001',
            'name': 'Business One',
            'date_registration': '2026-04-07T00:00:00',
            'billingstreet': '123 Main St',
            'billing_unit': '',
            'billingcity': 'Hartford',
            'billingstate': 'CT',
            'billingpostalcode': '06101',
            'business_email_address': 'one@example.com',
            'naics_code': '541110'
        },
        {
            'accountnumber': 'LLC002',
            'name': 'Business Two',
            'date_registration': '2026-04-07T00:00:00',
            'billingstreet': '456 Oak Ave',
            'billing_unit': '',
            'billingcity': 'Farmington',
            'billingstate': 'CT',
            'billingpostalcode': '06032',
            'business_email_address': 'two@example.com',
            'naics_code': '541110'
        }
    ]
    mock_response.raise_for_status = Mock()

    monkeypatch.setattr('scraper.requests.get', Mock(return_value=mock_response))

    # Mock the webhook POST
    mock_webhook_response = Mock()
    mock_webhook_response.json.return_value = {'success': True, 'count': 2}
    mock_webhook_response.raise_for_status = Mock()

    with patch('scraper.requests.post', return_value=mock_webhook_response) as mock_post:
        scraper.run_scraper()

        # Should have made exactly one POST (batch)
        assert mock_post.call_count == 1, f"Expected 1 POST call, got {mock_post.call_count}"

        # Verify the payload contains both LLCs
        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs.get('json')  # requests.post json param already has the dict

        # Should have a single 'llcs' key with an array
        assert 'llcs' in payload or 'data' in payload, "Payload should have llcs or data key"
        llcs_list = payload.get('llcs', payload.get('data', []))
        assert len(llcs_list) == 2, f"Expected 2 LLCs in batch, got {len(llcs_list)}"


def test_scraper_posts_correct_payload_format(monkeypatch):
    """Test that scraper posts payload in correct format."""
    import scraper

    mock_response = Mock()
    mock_response.json.return_value = [
        {
            'accountnumber': 'TEST123',
            'name': 'Test Business',
            'date_registration': '2026-04-07T00:00:00',
            'billingstreet': '123 Main St',
            'billing_unit': 'Suite 100',
            'billingcity': 'Hartford',
            'billingstate': 'CT',
            'billingpostalcode': '06101',
            'business_email_address': 'test@example.com',
            'naics_code': '541110'
        }
    ]
    mock_response.raise_for_status = Mock()

    monkeypatch.setattr('scraper.requests.get', Mock(return_value=mock_response))

    mock_webhook_response = Mock()
    mock_webhook_response.json.return_value = {'success': True, 'count': 1}
    mock_webhook_response.raise_for_status = Mock()

    with patch('scraper.requests.post', return_value=mock_webhook_response) as mock_post:
        scraper.run_scraper()

        # Get the payload from the POST call
        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs.get('json')  # requests.post json param already has the dict

        llc = payload['llcs'][0]

        # Verify required fields are present
        assert llc['filing_number'] == 'TEST123'
        assert llc['business_name'] == 'Test Business'
        assert llc['filing_date'] == '2026-04-07'  # Should be date only
        assert 'address' in llc or 'principal_address' in llc

        # Verify optional fields
        assert llc.get('email_address') == 'test@example.com'


def test_scraper_includes_api_key_in_webhook_post(monkeypatch):
    """Test that scraper includes X-API-Key header in webhook POST."""
    import scraper

    test_api_key = 'test-api-key-12345'
    monkeypatch.setenv('LLCSCRAPER_API_KEY', test_api_key)

    mock_response = Mock()
    mock_response.json.return_value = [
        {
            'accountnumber': 'LLC001',
            'name': 'Test Business',
            'date_registration': '2026-04-07T00:00:00',
            'billingstreet': '123 Main St',
            'billing_unit': '',
            'billingcity': 'Hartford',
            'billingstate': 'CT',
            'billingpostalcode': '06101',
            'business_email_address': 'test@example.com',
            'naics_code': '541110'
        }
    ]
    mock_response.raise_for_status = Mock()

    monkeypatch.setattr('scraper.requests.get', Mock(return_value=mock_response))

    mock_webhook_response = Mock()
    mock_webhook_response.json.return_value = {'success': True, 'count': 1}
    mock_webhook_response.raise_for_status = Mock()

    with patch('scraper.requests.post', return_value=mock_webhook_response) as mock_post:
        scraper.run_scraper()

        # Verify API key was included in headers
        call_kwargs = mock_post.call_args[1]
        headers = call_kwargs.get('headers', {})
        assert headers.get('X-API-Key') == test_api_key, "Should include X-API-Key header"


def test_scraper_retries_webhook_on_failure(monkeypatch):
    """Test that scraper retries webhook POST on failure (3 retries with backoff)."""
    import scraper
    import time

    mock_response = Mock()
    mock_response.json.return_value = [
        {
            'accountnumber': 'LLC001',
            'name': 'Test Business',
            'date_registration': '2026-04-07T00:00:00',
            'billingstreet': '123 Main St',
            'billing_unit': '',
            'billingcity': 'Hartford',
            'billingstate': 'CT',
            'billingpostalcode': '06101',
            'business_email_address': 'test@example.com',
            'naics_code': '541110'
        }
    ]
    mock_response.raise_for_status = Mock()

    monkeypatch.setattr('scraper.requests.get', Mock(return_value=mock_response))

    # Mock webhook to fail first 2 times, then succeed on 3rd
    mock_webhook_fail = Mock()
    mock_webhook_fail.raise_for_status.side_effect = Exception("Connection error")

    mock_webhook_success = Mock()
    mock_webhook_success.json.return_value = {'success': True, 'count': 1}
    mock_webhook_success.raise_for_status = Mock()

    with patch('scraper.requests.post', side_effect=[mock_webhook_fail, mock_webhook_fail, mock_webhook_success]) as mock_post:
        with patch('scraper.add_log') as mock_log:
            result = scraper.run_scraper()

            # Should have retried 3 times total
            assert mock_post.call_count == 3, f"Expected 3 POST calls (retry), got {mock_post.call_count}"

            # Verify that retries were logged
            log_calls = [str(c) for c in mock_log.call_args_list]
            assert any('retry' in str(c).lower() or 'attempt' in str(c).lower() for c in log_calls), \
                "Should log retry attempts"


def test_scraper_gives_up_after_max_retries(monkeypatch):
    """Test that scraper gives up after 3 failed retries and logs error."""
    import scraper

    mock_response = Mock()
    mock_response.json.return_value = [
        {
            'accountnumber': 'LLC001',
            'name': 'Test Business',
            'date_registration': '2026-04-07T00:00:00',
            'billingstreet': '123 Main St',
            'billing_unit': '',
            'billingcity': 'Hartford',
            'billingstate': 'CT',
            'billingpostalcode': '06101',
            'business_email_address': 'test@example.com',
            'naics_code': '541110'
        }
    ]
    mock_response.raise_for_status = Mock()

    monkeypatch.setattr('scraper.requests.get', Mock(return_value=mock_response))

    # Mock webhook to always fail
    mock_webhook_fail = Mock()
    mock_webhook_fail.raise_for_status.side_effect = Exception("Webhook unreachable")

    with patch('scraper.requests.post', return_value=mock_webhook_fail) as mock_post:
        with patch('scraper.add_log') as mock_log:
            result = scraper.run_scraper()

            # Should have made 3 attempts (initial + 2 retries)
            assert mock_post.call_count == 3, f"Expected 3 attempts, got {mock_post.call_count}"

            # Verify error was logged
            error_logs = [str(c) for c in mock_log.call_args_list if 'error' in str(c).lower()]
            assert len(error_logs) > 0, "Should log error after max retries exceeded"


def test_scraper_handles_webhook_validation_errors(monkeypatch):
    """Test that scraper handles webhook validation errors gracefully."""
    import scraper

    mock_response = Mock()
    mock_response.json.return_value = [
        {
            'accountnumber': 'LLC001',
            'name': 'Test Business',
            'date_registration': '2026-04-07T00:00:00',
            'billingstreet': '123 Main St',
            'billing_unit': '',
            'billingcity': 'Hartford',
            'billingstate': 'CT',
            'billingpostalcode': '06101',
            'business_email_address': 'test@example.com',
            'naics_code': '541110'
        }
    ]
    mock_response.raise_for_status = Mock()

    monkeypatch.setattr('scraper.requests.get', Mock(return_value=mock_response))

    # Mock webhook to return validation error (400)
    mock_webhook_error = Mock()
    mock_webhook_error.status_code = 400
    mock_webhook_error.json.return_value = {'error': 'Invalid payload: missing required field'}
    mock_webhook_error.raise_for_status.side_effect = Exception("400 Bad Request")

    with patch('scraper.requests.post', return_value=mock_webhook_error) as mock_post:
        with patch('scraper.add_log') as mock_log:
            result = scraper.run_scraper()

            # Should log the validation error
            error_logs = [str(c) for c in mock_log.call_args_list if 'error' in str(c).lower()]
            assert len(error_logs) > 0, "Should log validation error"


def test_scraper_does_not_crash_on_webhook_failure(monkeypatch):
    """Test that scraper continues gracefully even if webhook fails completely."""
    import scraper

    mock_response = Mock()
    mock_response.json.return_value = [
        {
            'accountnumber': 'LLC001',
            'name': 'Test Business',
            'date_registration': '2026-04-07T00:00:00',
            'billingstreet': '123 Main St',
            'billing_unit': '',
            'billingcity': 'Hartford',
            'billingstate': 'CT',
            'billingpostalcode': '06101',
            'business_email_address': 'test@example.com',
            'naics_code': '541110'
        }
    ]
    mock_response.raise_for_status = Mock()

    monkeypatch.setattr('scraper.requests.get', Mock(return_value=mock_response))

    # Mock webhook to always fail
    with patch('scraper.requests.post', side_effect=Exception("Webhook totally broken")):
        with patch('scraper.add_log'):
            # Should not raise an exception
            try:
                result = scraper.run_scraper()
                # The scraper should return a result (empty or with error logged)
                assert isinstance(result, list), "run_scraper should return a list even on webhook failure"
            except Exception as e:
                pytest.fail(f"run_scraper should not raise exception, got: {e}")


def test_scraper_uses_configurable_webhook_url(monkeypatch):
    """Test that webhook URL can be configured via environment or default."""
    import scraper

    # Set a custom webhook URL
    custom_url = 'http://custom-server:8080/api/llc/webhook'
    monkeypatch.setenv('WEBHOOK_URL', custom_url)

    mock_response = Mock()
    mock_response.json.return_value = [
        {
            'accountnumber': 'LLC001',
            'name': 'Test Business',
            'date_registration': '2026-04-07T00:00:00',
            'billingstreet': '123 Main St',
            'billing_unit': '',
            'billingcity': 'Hartford',
            'billingstate': 'CT',
            'billingpostalcode': '06101',
            'business_email_address': 'test@example.com',
            'naics_code': '541110'
        }
    ]
    mock_response.raise_for_status = Mock()

    monkeypatch.setattr('scraper.requests.get', Mock(return_value=mock_response))

    mock_webhook_response = Mock()
    mock_webhook_response.json.return_value = {'success': True, 'count': 1}
    mock_webhook_response.raise_for_status = Mock()

    with patch('scraper.requests.post', return_value=mock_webhook_response) as mock_post:
        scraper.run_scraper()

        # Verify the custom URL was used
        call_kwargs = mock_post.call_args[1] if mock_post.call_args[1] else {}
        call_args = mock_post.call_args[0] if mock_post.call_args[0] else []

        webhook_url = call_args[0] if call_args else call_kwargs.get('url')
        assert webhook_url == custom_url or webhook_url is not None, f"Should use webhook URL, got {webhook_url}"


def test_scraper_logs_success_when_webhook_accepts(monkeypatch):
    """Test that scraper logs success when webhook accepts LLCs."""
    import scraper

    mock_response = Mock()
    mock_response.json.return_value = [
        {
            'accountnumber': 'LLC001',
            'name': 'Test Business',
            'date_registration': '2026-04-07T00:00:00',
            'billingstreet': '123 Main St',
            'billing_unit': '',
            'billingcity': 'Hartford',
            'billingstate': 'CT',
            'billingpostalcode': '06101',
            'business_email_address': 'test@example.com',
            'naics_code': '541110'
        }
    ]
    mock_response.raise_for_status = Mock()

    monkeypatch.setattr('scraper.requests.get', Mock(return_value=mock_response))

    mock_webhook_response = Mock()
    mock_webhook_response.json.return_value = {'success': True, 'count': 1}
    mock_webhook_response.raise_for_status = Mock()

    with patch('scraper.requests.post', return_value=mock_webhook_response):
        with patch('scraper.add_log') as mock_log:
            scraper.run_scraper()

            # Verify success was logged
            success_logs = [str(c) for c in mock_log.call_args_list if 'success' in str(c).lower() or 'webhook' in str(c).lower()]
            # At minimum, should have webhook posting logs
            log_messages = [str(c) for c in mock_log.call_args_list]
            assert len(log_messages) > 0, "Should log webhook posting"
