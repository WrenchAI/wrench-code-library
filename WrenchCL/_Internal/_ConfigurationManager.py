#  Copyright (c) $YEAR$. Copyright (c) $YEAR$ Wrench.AI., Willem van der Schans, Jeong Kim
#
#  MIT License
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#  All works within the Software are owned by their respective creators and are distributed by Wrench.AI.
#
#  For inquiries, please contact Willem van der Schans through the official Wrench.AI channels or directly via GitHub at [Kydoimos97](https://github.com/Kydoimos97).
#


import os
from pathlib import Path

from dotenv import load_dotenv

from ..Exceptions import InvalidConfigurationException
from ..Tools import logger

MISSING_KEYS_MESSAGE = """
Error in loading environment variables: Missing required key: 'SECRET_ARN'.

Required Variables:
    - SECRET_ARN: Required for fetching AWS secrets (mandatory).

Required When Overriding Defaults:
    - AWS_PROFILE: Optional; if the default AWS profile in ~/.aws/credentials is sufficient.
    - REGION_NAME: Optional; if the default region ('us-east-1') is sufficient.

SSH Tunnel Creation. Optional; (for RDS/Bastion):
    - SSH_SERVER: SSH server address.
    - SSH_PORT: SSH server port (defaults to 22 if not specified).
    - SSH_USER: SSH username (e.g., ec2-user).
    Authentication: Either one of the following is required:
        - PEM_PATH: Path to the PEM file for key-based SSH authentication.
        - SSH_PASSWORD: SSH password (optional if PEM_PATH is provided).

Predefined SSH Tunnel:
    - PGHOST_OVERRIDE: Optional; Overrides the host in the fetched secret to point to the active SSH tunnel (e.g., 127.0.0.1).
    - PGPORT_OVERRIDE: Optional; Overrides the port in the fetched secret to point to the active SSH tunnel (e.g., 7778).

------------------------
Example .env:

    SECRET_ARN=arn:aws:secretsmanager:us-east-1:123456789012:secret:example-secret-arn
        
    AWS_PROFILE=prod-creds
    REGION_NAME=us-east-1
    
    SSH_SERVER=example-ssh-server.com
    SSH_PORT=22
    SSH_USER=ec2-user
    
    PEM_PATH=/path/to/your/key.pem
    SSH_PASSWORD=your-ssh-password
    
    PGHOST_OVERRIDE=127.0.0.1
    PGPORT_OVERRIDE=7778
------------------------

Please ensure these keys are set either as environment variables or in a .env file. 
If using AWS_PROFILE, confirm the profile is defined in your ~/.aws/credentials file and ~/.aws/config file. 
If using SSH tunnels, ensure all required credentials are configured.
"""

class _ConfigurationManager:
    """
    Manages the configuration settings for the application, including AWS and OpenAI credentials, SSH details,
    and database batch size. Configurations can be initialized from environment files, environment variables,
    or keyword arguments.

    Attributes:
        env_path (str): The path to the environment file.
        aws_profile (str): AWS profile name for creating sessions.
        region_name (str): AWS region name.
        secret_arn (str): ARN of the AWS Secrets Manager secret.
        openai_api_key (str): API key for OpenAI.
        ssh_server (str): SSH server address.
        ssh_port (int): SSH server port.
        ssh_user (str): SSH username.
        ssh_password (str): SSH user password.
        pem_path (str): Path to the PEM file for SSH authentication.
        qa_host_check (str): Host check identifier for QA environment.
        dev_host_check (str): Host check identifier for DEV environment.
        prod_host_check (str): Host check identifier for PROD environment.
        db_batch_size (int): Batch size for database operations.
        aws_deployment (bool): Override for ssh tunnel on QA (when actively deployed on aws shh tunnel is off)
    """

    def __init__(self, env_path=None, **kwargs):
        """
        Initializes the ConfigurationManager by loading configurations from the specified environment file,
        environment variables, and keyword arguments.

        :param env_path: The path to the environment configuration file.
        :type env_path: str, optional
        :param kwargs: Additional configuration parameters.
        """
        self.env_path = env_path

        # Initialize default values
        self.aws_profile = None
        self.region_name = None
        self.secret_arn = None
        self.openai_api_key = None
        self.ssh_server = None
        self.ssh_port = None
        self.ssh_user = None
        self.ssh_password = None
        self.pem_path = None
        self.qa_host_check = 'ce5sivkxtgbs'
        self.dev_host_check = 'ced0khqdverl'
        self.prod_host_check = 'c3zncwpdk0m7'
        self.db_batch_size = 10000
        self.aws_deployment = None

        try:
            self._initialize_env()
        except Exception as e:
            logger.debug(f"No env file found to load, using existing variables. Error: {e}")
        self._init_from_env()
        self._init_from_kwargs(kwargs)

        if self.secret_arn is None:
            raise InvalidConfigurationException(
                config_name="Secret ARN",
                reason="Missing environment variable or configuration.",
                message=MISSING_KEYS_MESSAGE
            )


        # Log configuration after initialization
        logger.debug(self._log_safe_config())

    def _initialize_env(self):
        """
        Loads the environment variables from the specified .env file.
        """
        if self.env_path:
            env_path = self._resolve_path(self.env_path)
            load_dotenv(env_path, override=True)

    def _resolve_path(self, path):
        """
        Resolves the given path to an absolute path.

        :param path: The relative or absolute path.
        :type path: str
        :returns: The absolute path.
        :rtype: str
        """
        if Path(path).is_absolute():
            return path
        return os.path.join(os.getcwd(), path)

    def _init_from_kwargs(self, kwargs):
        """
        Initializes configuration values from keyword arguments.

        :param kwargs: Additional configuration parameters.
        :type kwargs: dict
        """
        self.aws_profile = kwargs.get('AWS_PROFILE', self.aws_profile)
        self.region_name = kwargs.get('REGION_NAME', self.region_name)
        self.secret_arn = kwargs.get('SECRET_ARN', self.secret_arn)
        self.openai_api_key = kwargs.get('OPENAI_API_KEY', self.openai_api_key)
        self.ssh_server = kwargs.get('SSH_SERVER', self.ssh_server)
        self.ssh_port = int(kwargs.get('SSH_PORT', self.ssh_port or 22))
        self.ssh_user = kwargs.get('SSH_USER', self.ssh_user)
        self.ssh_password = kwargs.get('SSH_PASSWORD', self.ssh_password)
        self.pem_path = kwargs.get('PEM_PATH', self.pem_path)
        self.db_batch_size = int(kwargs.get('DB_BATCH_OVERRIDE', self.db_batch_size or 10000))
        self.aws_deployment = str(kwargs.get('AWS_DEPLOYMENT', self.aws_deployment)).lower() == 'true'

    def _init_from_env(self):
        """
        Initializes configuration values from environment variables.
        """
        self.aws_profile = os.getenv('AWS_PROFILE', self.aws_profile)
        self.region_name = os.getenv('REGION_NAME', self.region_name)
        self.secret_arn = os.getenv('SECRET_ARN', self.secret_arn)
        self.openai_api_key = os.getenv('OPENAI_API_KEY', self.openai_api_key)
        self.ssh_server = os.getenv('SSH_SERVER', self.ssh_server)
        self.ssh_port = int(os.getenv('SSH_PORT', self.ssh_port or 22))
        self.ssh_user = os.getenv('SSH_USER', self.ssh_user)
        self.ssh_password = os.getenv('SSH_PASSWORD', self.ssh_password)
        self.pem_path = os.getenv('PEM_PATH', self.pem_path)
        self.db_batch_size = int(os.getenv('DB_BATCH_OVERRIDE', self.db_batch_size or 10000))
        self.aws_deployment = str(os.getenv('AWS_DEPLOYMENT', None)).lower() == 'true'

    def _log_safe_config(self):
        """
        Returns a safely masked version of the configuration for logging, masking sensitive fields.

        :returns: A dictionary of safely masked configuration values.
        :rtype: dict
        """
        def mask_sensitive(value):
            if value and isinstance(value, str) and len(value) > 6:
                return f"{value[:3]}...{value[-3:]}"
            return value

        return {
            'aws_profile': self.aws_profile,
            'region_name': self.region_name,
            'secret_arn': mask_sensitive(self.secret_arn),
            'openai_api_key': mask_sensitive(self.openai_api_key),
            'ssh_server': self.ssh_server,
            'ssh_port': self.ssh_port,
            'ssh_user': self.ssh_user,
            'ssh_password': mask_sensitive(self.ssh_password),
            'pem_path': mask_sensitive(self.pem_path),
            'qa_host_check': self.qa_host_check,
            'db_batch_size': self.db_batch_size,
            'aws_deployment': self.aws_deployment
        }