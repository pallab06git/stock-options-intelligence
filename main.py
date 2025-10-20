# © 2025 Pallab Basu Roy. All rights reserved.
# This source code is proprietary and confidential.
# Unauthorized copying, modification, or commercial use is strictly prohibited.
# Repository: https://github.com/pallab06/stock-options-intelligence

"""
Main entry point for Stock Options Intelligence
"""

import uvicorn

from src.config.settings import get_settings
from src.utils.logger import setup_logger

if __name__ == "__main__":
    settings = get_settings()

    # Setup logger
    logger = setup_logger(
        log_level=settings.log_level,
        log_file="logs/app.log",
    )

    logger.info(f"Starting Stock Options Intelligence in {settings.environment} mode")

    # Run the application
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.environment == "development",
        log_config=None,  # Use our custom logger
    )
