import os


def test_send_alert_sends_email(mocker):
    mock_resend = mocker.patch("scraper.alert.resend")
    mock_resend.Emails.send.return_value = {"id": "email-123"}

    from scraper.alert import send_alert
    send_alert("Pipeline falhou!\nErro: timeout")

    mock_resend.Emails.send.assert_called_once()
    call_args = mock_resend.Emails.send.call_args[0][0]
    assert "Pipeline falhou!" in call_args["text"]
    assert "[CD PRICE TRACKER]" in call_args["subject"]


def test_send_alert_catches_error(mocker):
    mocker.patch("scraper.alert.resend")
    from scraper.alert import send_alert
    send_alert("Test message")
