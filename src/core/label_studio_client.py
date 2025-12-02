from label_studio_sdk import Client
from env_config_init import settings

__all__ = ['label_studio_client']


class LABEL_STUDIO_CLIENT(Client):
    def __init__(self):
        super().__init__(url=settings.LABEL_STUDIO_URL, api_key=settings.LABEL_STUDIO_API_KEY)


label_studio_client = LABEL_STUDIO_CLIENT()
