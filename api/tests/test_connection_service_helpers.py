"""Secret handling in the connection service: redaction never leaks secrets;
merge retains a stored secret the client couldn't resend."""

from integrations import registry
from services.connection_service import merge_config, redact_config


def test_redact_hides_secret_values():
    spec = registry.get("monzo")
    config = {"access_token": "super-secret", "account_id": "acc_123"}
    redacted = redact_config(spec, config)

    assert "access_token" not in redacted            # secret value gone
    assert redacted["account_id"] == "acc_123"       # non-secret retained
    # access_token is set; the OAuth secrets are absent here.
    assert redacted["_secrets"] == {
        "access_token": True, "client_secret": False, "refresh_token": False,
    }


def test_redact_marks_unset_secret():
    spec = registry.get("monzo")
    redacted = redact_config(spec, {"account_id": "acc_123"})
    assert redacted["_secrets"] == {
        "access_token": False, "client_secret": False, "refresh_token": False,
    }


def test_merge_retains_existing_secret_when_omitted():
    spec = registry.get("monzo")
    existing = {"access_token": "stored-token", "account_id": "old"}
    # client resends non-secret fields + the _secrets marker, but no token value
    incoming = {"account_id": "new", "_secrets": {"access_token": True}}

    merged = merge_config(spec, existing, incoming)

    assert merged["access_token"] == "stored-token"  # kept
    assert merged["account_id"] == "new"             # updated
    assert "_secrets" not in merged                  # marker stripped


def test_merge_replaces_secret_when_new_value_given():
    spec = registry.get("monzo")
    existing = {"access_token": "old-token", "account_id": "a"}
    incoming = {"access_token": "new-token", "account_id": "a"}
    merged = merge_config(spec, existing, incoming)
    assert merged["access_token"] == "new-token"
