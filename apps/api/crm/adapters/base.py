from abc import ABC, abstractmethod


class BaseChannelAdapter(ABC):
    """Interface abstrata para adapters de canal de comunicação."""

    @abstractmethod
    def send(self, destination: str, message: str, subject: str = "") -> dict:
        """Envia mensagem para o destino.

        Retorna dict com {'success': bool, 'provider_id': str, 'error': str}.
        """
        pass

    @abstractmethod
    def channel_name(self) -> str:
        pass
