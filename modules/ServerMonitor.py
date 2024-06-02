"""
@File    :   ServerMonitorError.py
@Time    :   2024/05/18 22:56:36
@Author  :   Thomas Obarowski
@Version :   1.0
@Contact :   tjobarow@gmail.com
@Link    :   https://github.com/tjobarow
@License :   The MIT License 2024
@Description    :   Custom error class to raise when ServerMonitor throws
an error, but the caller just needs to know one happened
"""


class ServerMonitorError(Exception):
    def __init__(
        self,
        message: str = "This server monitor instance encountered an error.",
        errors=None,
    ):
        super().__init__(message)
        self.errors = errors


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
import logging
import logging.config
from xmlrpc.client import ServerProxy
from xmlrpc.client import ProtocolError


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

        self._logger.debug(
            f"Will attempt to init ServerProxy for {base_url}{api_endpoint}"
        )

        # Initiate connection to XMLRPC Server
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
        """This function will setup the XMLRPC connection to the provided XLM-RPC server

        Args:
            base_url (str): URL of the XML-RPC server (i.e http:myxmlrpcserver.com:9001)
            api_endpoint (str): The root path of the API (i.e /RPC2)
            api_user (str): User with permissions to access the API
            api_pwd (str): User with permissions to access the API

        Returns:
            ServerProxy: _description_
        """
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
            # Then we return a ServerProxy object that is configured with the auth
            # url
            return ServerProxy(
                uri=url_with_auth,
            )
        except TypeError as type_error:
            self._logger.critical(
                "A critical error occurred when attempting to create XMLRPC ServerProxy"
            )
            self._logger.critical(str(type_error))

    def get_all_process_info(self) -> list:
        """Returns a list of all processes under supervisor and information about them

        Raises:
            ServerMonitorError: If an error occurred during getAllProcessInfo call, it is caught locally
            and then raised as a ServerMonitorError for the calling function to handle
            ServerMonitorError: If an error occurred during getAllProcessInfo call, it is caught locally
            and then raised as a ServerMonitorError for the calling function to handle

        Returns:
            list: List of structures, each structure representing a process and it's info
        """
        # Make call to supervisor to get all process info. It returns a dict
        try:
            result = self.server.supervisor.getAllProcessInfo()
            self._logger.info(
                f"Successfully fetched process information for {len(result)} processes."
            )
            return result
        except ProtocolError as protocol_error:
            self._logger.critical(
                "The call to supervisor.getAllProcessInfo returned a 401 - Unauthorized. Please verify provided credentials are valid and have permission to use the API."
            )
            self._logger.critical(protocol_error)
            raise ServerMonitorError(
                "Getting all process information resulted in a 401 - Unauthorized. Please verify credentials are valid and have permissions to access the supervisor API."
            )
        except Exception as generic_error:
            # If an exception occurs, log the error, and raise a ServerMonitorError
            self._logger.error(
                f"An error occurred when attempting to get all process information."
            )
            self._logger.error(str(generic_error))
            # Raising this so the calling function can implement how to handle this failure
            raise ServerMonitorError(
                f"ServerMonitor encountered an error while trying to get all process information."
            )

    def start_process(self, process_name: str) -> bool:
        """Starts a process given a process name

        Args:
            process_name (str): Name of the process to pass to the supervisor.startProcess RPC call

        Raises:
            ValueError: If the process_name is invalid this is raised and caught locally
            Exception: If the call to supervisor.startProcess returned False, that indicates a fault, so we raise this generic exception, which is caught locally
            ServerMonitorError: Raised to calling function so it can decide how to handle the error
            ServerMonitorError: Raised to calling function so it can decide how to handle the error
            ServerMonitorError: Raised to calling function so it can decide how to handle the error

        Returns:
            bool: True if process started successfully
        """
        try:
            # If a blank process_name was provided, or None was provided
            if (len(process_name) == 0) or (process_name is None):
                raise ValueError
            # Make call to supervisor to start a process
            result = self.server.supervisor.startProcess(process_name, True)
            if result:
                self._logger.info(
                    f"Process name {process_name} was started successfully."
                )
                return result
            else:
                raise Exception(
                    f"The supervisor.startProcess({process_name}) call returned False, indicating a fault occurred."
                )
        # ValueError should only occur when the process_name was invalid
        except ValueError:
            self._logger.error(
                f"The value provided for 'process_name: str' was invalid: {process_name}"
            )
            # Raising this so the calling function can implement how to handle this failure
            raise ServerMonitorError(
                f"The value provided for 'process_name: str' was invalid: {process_name}"
            )
        except ProtocolError as protocol_error:
            self._logger.critical(
                "The call to supervisor.startProcess returned a 401 - Unauthorized. Please verify provided credentials are valid and have permission to use the API."
            )
            self._logger.critical(protocol_error)
            raise ServerMonitorError(
                f"API call to start {process_name} resulted in a 401 - Unauthorized. Please verify credentials are valid and have permissions to access the supervisor API."
            )
        # Should only occur if the supervisor startProcess call itself fails
        except Exception as generic_error:
            self._logger.error(
                f"An error occurred when attempting to start process {process_name}"
            )
            self._logger.error(str(generic_error))
            # Raising this so the calling function can implement how to handle this failure
            raise ServerMonitorError(
                f"ServerMonitor encountered an error while trying to start process {process_name}"
            )

    def stop_process(self, process_name: str) -> bool:
        """Calls supervisor.stopProcess(process_name) to stop the process_name provided.

        Args:
            process_name (str): Name of process to stop

        Raises:
            ValueError: If the process_name is invalid this is raised and caught locally
            Exception: If the call to supervisor.stopProcess returned False, that indicates a fault, so we raise this generic exception, which is caught locally
            ServerMonitorError: Raised to calling function so it can decide how to handle the error
            ServerMonitorError: Raised to calling function so it can decide how to handle the error

        Returns:
            bool: True if process stopped successfully
        """
        try:
            # If a blank process_name was provided, or None was provided
            if (len(process_name) == 0) or (process_name is None):
                raise ValueError
            # Make call to supervisor to stop a process
            result = self.server.supervisor.stopProcess(process_name, True)
            if result:
                self._logger.info(
                    f"Process name {process_name} was stopped successfully."
                )
                return result
            else:
                raise Exception(
                    f"The supervisor.stopProcess({process_name}) call returned a False result, indicating a fault occurred."
                )
        # ValueError should only occur when the process_name was invalid
        except ValueError:
            self._logger.error(
                f"The value provided for 'process_name: str' was invalid: {process_name}"
            )
            # Raising this so the calling function can implement how to handle this failure
            raise ServerMonitorError(
                f"The value provided for 'process_name: str' was invalid: {process_name}"
            )
        except ProtocolError as protocol_error:
            self._logger.critical(
                "The call to supervisor.getAllProcessInfo returned a 401 - Unauthorized. Please verify provided credentials are valid and have permission to use the API."
            )
            self._logger.critical(protocol_error)
            raise ServerMonitorError(
                "Getting all process information resulted in a 401 - Unauthorized. Please verify credentials are valid and have permissions to access the supervisor API."
            )
        # Should only occur if the supervisor stopProcess call itself fails
        except Exception as generic_error:
            self._logger.error(
                f"An error occurred when attempting to stop process {process_name}"
            )
            self._logger.error(str(generic_error))
            # Raising this so the calling function can implement how to handle this failure
            raise ServerMonitorError(
                f"ServerMonitor encountered an error while trying to stop process {process_name}"
            )

    def restart_process(self, process_name: str) -> bool:
        """Uses the existing self.stop_process and self.start_process functions to
        restart the process provided in process_name

        Args:
            process_name (str): Name of the process to restart

        Raises:
            ValueError: Raised and caught locally if process_name is invalid
            ServerMonitorError: If self.stop_process or self.start_process fail, they will raise a ServerMonitorError to local try/except block
            server_mon_error: The above caught ServerMonitorError will be raised to the calling function for handling.

        Returns:
            bool: True if the process restarted. Other wise an error was likely raised.
        """
        try:
            # If a blank process_name was provided, or None was provided
            if (len(process_name) == 0) or (process_name is None):
                raise ValueError
            # Use the already implemented stop/start functions
            self.stop_process(process_name=process_name)
            self.start_process(process_name=process_name)
            self._logger.info(
                f"Process name {process_name} was restarted successfully."
            )
            return True
        # ValueError should only occur when the process_name was invalid
        except ValueError:
            self._logger.error(
                f"The value provided for 'process_name: str' was invalid: {process_name}"
            )
            # Raising this so the calling function can implement how to handle this failure
            raise ServerMonitorError(
                f"The value provided for 'process_name: str' was invalid: {process_name}"
            )
        # Should only occur if the supervisor restartProcess call itself fails
        except ServerMonitorError as server_mon_error:
            self._logger.error(
                f"An error occurred when attempting to restart process {process_name}"
            )
            self._logger.error(str(server_mon_error))
            # Raising this so the calling function can implement how to handle this failure
            raise server_mon_error
