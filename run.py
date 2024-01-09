import asyncio
import yaml

from database import initialize_database
from loguru import logger
from src.main import LowaOffendersScraper


def validate_config() -> dict:
    with open("settings.yaml", "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    if "two_captcha_api_key" not in config:
        logger.error("Two captcha api key is not provided")
        exit(1)


    return config



async def run() -> None:
    config = validate_config()

    scraper = LowaOffendersScraper(config=config)
    await initialize_database()
    await scraper.start()


if __name__ == '__main__':
    asyncio.run(run())
