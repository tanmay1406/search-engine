import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    # MongoDB configuration
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    
    # Defaults for Master
    MASTER_IP = os.getenv('MASTER_IP', 'localhost:50051')
    BACKUP_IP = os.getenv('BACKUP_IP', 'localhost:50063')
    CRAWLER_IP = os.getenv('CRAWLER_IP', 'localhost:50060')
    
    # Replica file configuration
    REPLICAS_LIST_FILE = os.getenv('REPLICAS_LIST_FILE', 'replicas_list.txt')
    
config = Config()
