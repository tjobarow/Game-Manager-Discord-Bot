"""
@File    :   run_server_monitor.py
@Time    :   2024/05/17 23:53:12
@Author  :   Thomas Obarowski
@Version :   1.0
@Contact :   tjobarow@gmail.com
@Link    :   https://github.com/tjobarow
@License :   The MIT License 2024
@Description    :   INSERT DESCRIPTION
"""

# Import custom packages
from modules.ServerMonitor import ServerMonitor, ServerMonitorError

# Import built-in packages
import os
import sys
import json
import time
from datetime import datetime
import logging
import logging.config
from xmlrpc.client import ServerProxy


# Import 3rd party packages
from dotenv import load_dotenv

load_dotenv("./config/.server-env")


def create_logger() -> logging.Logger:
    """_summary_

    Returns:
        logging.Logger: _description_
    """
    # Prepare logging configuration
    logging_config_path: str = os.getenv("logging_config_filepath")
    print(f"Will load logging configuration from {logging_config_path}")
    try:
        with open(logging_config_path, "rt") as file:
            all_config = json.load(file)
            config = all_config["ValheimServerMonitor"]
        # Renames the log file
        config["handlers"]["file"]["filename"] = os.path.join(
            os.path.dirname(__file__),
            f"./logs/{__name__}_{datetime.now().strftime('YYYY-mm-dd')}.log",
        )
        # Pass the config dict to this method to load a logger based on the config
        logging.config.dictConfig(config)
        return logging.getLogger(name="ValheimServerMonitor")
    except FileNotFoundError:
        print(f"Unable to find logging configuration at {logging_config_path}...")
        sys.exit(1)
    except Exception as err:
        print(f"An error occurred when attempting to create the logger object.\n{err}")
        sys.exit(1)


if __name__ == "__main__":
    logger = create_logger()
    try:
        ValheimServerMonitor = ServerMonitor(
            base_url=os.getenv("base_url"),
            api_endpoint=os.getenv("api_endpoint"),
            api_user=os.getenv("api_user"),
            api_pwd=os.getenv("api_pwd"),
        )

        print(json.dumps(ValheimServerMonitor.get_all_process_info(), indent=4))
        print(ValheimServerMonitor.restart_process("valheim-server"))
    except ServerMonitorError as sm_err:
        logger.info(sm_err)
