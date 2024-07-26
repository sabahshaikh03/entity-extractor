import logging
from sqlalchemy.orm import sessionmaker
from app.modules.entity_extractor.services.artifact_entity_extractor import ArtifactEntityExtractor
from connectors.mysql_connector import MySQLConnector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize SQLAlchemy session
mysql_connector = MySQLConnector()
Session = sessionmaker(bind=mysql_connector.engine)
session = Session()

# Initializing the ArtifactEntityExtractor
extractor = ArtifactEntityExtractor(logger, session)

# Local PDF file path for testing
local_pdf_path = "C:\\Users\\Shireen\\Desktop\\ingestion\\ingestion\\experiment\\test_docs\\Cadmium Nitrate_by Chem Service_SDS_S-M.pdf"

# Mock artifact_id for testing
artifact_id = '297e0382905eab7401905eac528d0000'

# Simulate the extraction process
response = extractor.extract_entity(artifact_id)

# Print the response for verification
print(response)

# Close the session
session.close()
