from config import Settings, settings


def test_default_environment_is_production():
    defaults = Settings(_env_file=None)
    assert defaults.environment == "production"

def test_default_provider_credentials_are_blank_or_local():
    defaults = Settings(_env_file=None)
    assert defaults.trading_212_key == "local"
    assert defaults.coinbase_api_key_name == ""
    assert defaults.coinbase_api_private_key == ""
    assert defaults.monzo_access_token == ""
    assert defaults.monzo_account_id == ""


def test_default_monzo_projection_assumptions_are_zero():
    defaults = Settings(_env_file=None)
    assert defaults.monzo_pots_monthly_contribution == 0.0
    assert defaults.monzo_pots_growth_rate == 0.0


def test_default_snapshot_scheduler_settings():
    assert settings.snapshot_scheduler_enabled is True
    assert settings.snapshot_time == "00:30"


def test_settings_ignores_unknown_env_vars(monkeypatch):
    monkeypatch.setenv("SOME_UNRELATED_VARIABLE", "whatever")
    unrelated_settings = Settings()
    assert not hasattr(unrelated_settings, "some_unrelated_variable")


def test_settings_reads_environment_override(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    dev_settings = Settings()
    assert dev_settings.environment == "development"
