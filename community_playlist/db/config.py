import os
from dotenv import load_dotenv



dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../..", ".env"))
load_dotenv(dotenv_path)

sqluser = os.getenv('MYSQL_USER')
sqlpass = os.getenv('MYSQL_PASS')