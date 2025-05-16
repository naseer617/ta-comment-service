# Step 1: Create virtual env
python3 -m venv .venv

# Step 2: Activate it
source .venv/bin/activate

# Step 3: Install dependencies
pip install -r requirements.txt
pip install -r tests/test-config/requirements-dev.txt