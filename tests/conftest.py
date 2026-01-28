# Test configuration
import os

# Disable metrics in tests
os.environ['ENABLE_METRICS'] = 'false'