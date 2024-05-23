"""
@File    :   server_monitor.py
@Time    :   2024/05/17 23:37:33
@Author  :   Thomas Obarowski
@Version :   1.0
@Contact :   tjobarow@gmail.com
@Link    :   https://github.com/tjobarow
@License :   The MIT License 2024
@Description    :   INSERT DESCRIPTION
"""

# Import built-in packages
import os
import re
import sys
import json
import time
import base64
import logging
import logging.config
from xmlrpc.client import ServerProxy


# Import 3rd party packages
from dotenv import load_dotenv

load_dotenv("./config/.env")


class ServerMonitor:

    def __init__(self, base_url: str, api_endpoint: str, api_user: str, api_pwd: str):
        # Get sublogger from ValheimServerMonitor
        self._logger = logging.getLogger("ValheimServerMonitor.ServerMonitor")

        self._logger.info("Initializing Server Monitor...")

        # Validate value of base_url not empty or None
        if (len(base_url) == 0) or base_url is None:
            raise ValueError("The value provided for 'base_url' is not valid.")

        # Validate the base_url is of format "http[s]://*"
        http_re: re = re.compile(r"http(s?)://")
        if not re.match(pattern=http_re, string=base_url):
            raise ValueError(
                "The value provided for 'base_url' does not begin with http:// or https://"
            )

        # Validate value of api_endpoint not empty or None
        if (len(api_endpoint) == 0) or api_endpoint is None:
            raise ValueError("The value provided for 'api_endpoint' is not valid.")

        # Validate value of api_user not empty or None
        if (len(api_user) == 0) or api_user is None:
            raise ValueError("The value provided for 'api_user' is not valid.")

        # Validate value of api_pwd not empty or None
        if (len(api_pwd) == 0) or api_pwd is None:
            raise ValueError("The value provided for 'api_pwd' is not valid.")

        # Get ServerProxy
        self._logger.debug(
            f"Will attempt to init ServerProxy for {base_url}{api_endpoint}"
        )
        self.server = self.__init_xmlrpc_server__(
            base_url=base_url,
            api_endpoint=api_endpoint,
            api_user=api_user,
            api_pwd=api_pwd,
        )
        self._logger.debug("Initialized ServerProxy connection")

    def __init_xmlrpc_server__(
        self, base_url: str, api_endpoint: str, api_user: str, api_pwd: str
    ) -> ServerProxy:
        try:
            self._logger.debug(
                f"Will attempt to establish XMLRPC connection to {base_url}{api_endpoint}"
            )
            # We pass basic auth by prepending user:pwd behind http/https
            # but before the remote servers hostname
            # e.g http://user:password@remote_host.com/RPC

            # So here we have to split the base_url into just the hostname
            # based  on if its http or https
            if re.match(pattern=r"https://", string=base_url):
                remote_hostname: str = base_url[8::]
                http_meth: str = "https://"
            else:
                remote_hostname: str = base_url[7::]
                http_meth: str = "http://"
            # Then we have to reconstruct a new URL with auth details
            url_with_auth: str = (
                f"{http_meth}{api_user}:{api_pwd}@{remote_hostname}{api_endpoint}"
            )
            return ServerProxy(
                uri=url_with_auth,
            )
        except TypeError as type_error:
            self._logger.critical(
                "A critical error occurred when attempting to create XMLRPC ServerProxy"
            )
            self._logger.critical(str(type_error))

    def get_all_process_info(self) -> list:
        return self.server.supervisor.getAllProcessInfo()
