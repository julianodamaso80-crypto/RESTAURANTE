import structlog

from .base import BaseChannelAdapter

log = structlog.get_logger()


class StubChannelAdapter(BaseChannelAdapter):
    """Adapter stub para desenvolvimento e testes.

    Não envia nada — apenas loga.
    Substituir por adapters reais (Twilio, SendGrid, etc.) em produção.
    """

    def __init__(self, channel: str):
        self._channel = channel

    def channel_name(self) -> str:
        return self._channel

    def send(self, destination: str, message: str, subject: str = "") -> dict:
        log.info(
            "stub_adapter_send",
            channel=self._channel,
            destination=destination[:4] + "****",  # não logar destino completo
            message_length=len(message),
        )
        return {
            "success": True,
            "provider_id": f"stub_{self._channel}_{destination[:6]}",
            "error": "",
        }


def get_adapter(channel: str) -> BaseChannelAdapter:
    """Factory de adapters por canal.

    Em produção, trocar StubChannelAdapter por adapters reais.
    """
    return StubChannelAdapter(channel)
