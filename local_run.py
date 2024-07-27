import logging
import pickle
from app.modules.entity_extractor.services.artifact_entity_extractor import ArtifactEntityExtractor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initializing the ArtifactEntityExtractor
extractor = ArtifactEntityExtractor(logger)

# Mock artifact_id for testing
artifact_id = '297e0382909097e4019090c06bbb0001'

# Simulate the extraction process
response = extractor.extract_entity(artifact_id)

# Define the path to save the pickle file
pickle_file_path = r'C:\Users\Shireen\Downloads\response.pkl'

# Save the response to a pickle file
with open(pickle_file_path, 'wb') as pickle_file:
    pickle.dump(response, pickle_file)

# Log that the response was saved successfully
logger.info(f'Response saved to {pickle_file_path}')
