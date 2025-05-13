import json
import os

# Define data directory
DATA_DIR = 'data'
os.makedirs(DATA_DIR, exist_ok=True)

# Create empty data files
empty_dict = {}
for filename in ['auctions.json', 'bids.json', 'auction_results.json']:
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        with open(filepath, 'w') as f:
            json.dump(empty_dict, f)
        print(f"Created empty {filepath}")
    else:
        print(f"File already exists: {filepath}")
