from ccap.settings import Settings


def make_settings(allowed_emails: str) -> Settings:
    return Settings(
        database_url="postgresql+psycopg://x@127.0.0.1/x",
        session_secret="s" * 32,
        google_client_id="id",
        google_client_secret="secret",
        allowed_emails=allowed_emails,
    )


def test_empty_allowed_emails_rejects_everyone() -> None:
    settings = make_settings("")

    assert not settings.is_email_allowed("persona@example.com")


def test_allowed_emails_ignore_case_and_spaces() -> None:
    settings = make_settings(" Persona@Example.com , otra@example.com")

    assert settings.is_email_allowed("PERSONA@example.COM")


def test_email_outside_the_list_is_rejected() -> None:
    settings = make_settings("persona@example.com")

    assert not settings.is_email_allowed("intrusa@example.com")


def test_trailing_slash_is_removed_from_app_url() -> None:
    settings = Settings(
        database_url="postgresql+psycopg://x@127.0.0.1/x",
        session_secret="s" * 32,
        google_client_id="id",
        google_client_secret="secret",
        app_url="http://localhost:8000/",
    )

    assert settings.app_url == "http://localhost:8000"
