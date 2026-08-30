"""Central project configuration.

Secrets and environment-specific values are loaded from a ``.env`` file (see
`.env.example`) so that no credentials or machine-specific values are
committed to the repository.
"""

from pathlib import Path
import os

from dotenv import load_dotenv
from web3 import Web3


# ==============================
# Environment (values from .env)
# ==============================

# Load .env from the project root (parent of this scripts/ folder).
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


# ==============================
# Ganache Configuration
# ==============================

# Explicitly configured RPC URLs (optional). Supports both RPC_URL (primary)
# and GANACHE_URLS (comma-separated). Falls back to the default Ganache ports.
_RPC_URL_RAW = os.getenv("RPC_URL", "").strip()
_GANACHE_URLS_RAW = os.getenv("GANACHE_URLS", "").strip()

GANACHE_URLS = (
    [url.strip() for url in (_RPC_URL_RAW or _GANACHE_URLS_RAW).split(",") if url.strip()]
    or [
        "http://127.0.0.1:7545",
        "http://127.0.0.1:8545",
    ]
)

SOLC_VERSION = os.getenv("SOLC_VERSION", "0.8.0")

# The wallet address used to deploy the contracts and act as global admin.
# Override it in .env to match your own Ganache workspace; otherwise the
# deployment script will refuse to run to avoid guessing a wrong address.
FIXED_ADMIN_ADDRESS = os.getenv("ADMIN_ADDRESS", "")

# Admin password used by the CLI and GUI applications. This is intended for a
# local, demo-only environment. It is NOT real security: the smart contract
# itself is the source of authority for admin operations. Must be provided in
# .env - there is intentionally no hardcoded default.
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

# Optional block explorer base URL (e.g. a Ganache/Truffle explorer). When set,
# the GUI renders "View transaction on explorer" links. Leave empty on a plain
# Ganache workspace.
EXPLORER_URL = os.getenv("EXPLORER_URL", "").strip()


# ==============================
# Project Paths
# ==============================

CONTRACTS_DIR = BASE_DIR / "contracts"
OUTPUTS_DIR = BASE_DIR / "outputs"

REPORT_CARD_SOL = CONTRACTS_DIR / "ReportCard.sol"
GRADE_COIN_SOL = CONTRACTS_DIR / "ReportCardMember2.sol"

CONTRACT_ADDRESSES_FILE = OUTPUTS_DIR / "contract_addresses.json"

REPORT_CARD_ABI_FILE = OUTPUTS_DIR / "ReportCard_abi.json"
GRADE_COIN_ABI_FILE = OUTPUTS_DIR / "GradeCoin_abi.json"


# ==============================
# Ganache Connection
# ==============================

def connect_to_ganache():
    """Return ``(w3, url)`` connected to the first reachable Ganache node."""
    last_error = None

    for url in GANACHE_URLS:
        w3 = Web3(Web3.HTTPProvider(url))

        if w3.is_connected():
            print(f"Connected to Ganache: {url}")
            return w3, url

        last_error = url

    raise ConnectionError(
        "Failed to connect to Ganache. Start Ganache and check the RPC port "
        f"({', '.join(GANACHE_URLS)}). Last tried: {last_error}."
    )
