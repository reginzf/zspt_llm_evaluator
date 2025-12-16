from label_studio_sdk import Client
from env_config_init import settings

__all__ = ['label_studio_client']

label_studio_client = Client(url=settings.LABEL_STUDIO_URL, api_key=settings.LABEL_STUDIO_API_KEY)
