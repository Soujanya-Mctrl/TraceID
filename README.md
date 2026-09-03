# FaceScan-Blockchain-Verification 🛡️🔗

> **HH Goa 2026 Shortlisting Task 3**: Face Identification & Blockchain Verification  
> An end-to-end pipeline that takes a human face scan as input, identifies matching content across the web/social media through genuine visual search, and cryptographically anchors & verifies that discovered data on an immutable blockchain ledger.

---

## 📋 Table of Contents
- [Pipeline Architecture](#-pipeline-architecture)
- [Module Breakdown](#-module-breakdown)
  - [Part 1: Face Detection & Encoding](#part-1-face-detection--encoding)
  - [Part 2: Web & Social Media Search](#part-2-web--social-media-search)
  - [Part 3: Blockchain Verification](#part-3-blockchain-verification)
  - [Part 4: Glue Pipeline Orchestrator](#part-4-glue-pipeline-orchestrator)
- [Which Blockchain is Used?](#-which-blockchain-is-used)
- [Smart Contract Architecture](#-smart-contract-architecture)
- [Installation & Setup](#-installation--setup)
- [How to Run](#-how-to-run)
  - [1. Run the End-to-End Glue Script](#1-run-the-end-to-end-glue-script)
  - [2. Demonstrate Tamper-Evidence](#2-demonstrate-tamper-evidence)
  - [3. Run Individual Components Standalone](#3-run-individual-components-standalone)
- [Running Automated Tests](#-running-automated-tests)
- [Known Limitations](#-known-limitations)
- [Submission & Video Recording Checklist](#-submission--video-recording-checklist)

---

## 🚀 Pipeline Architecture

The pipeline strictly follows the required 4-stage dataflow:

```
[ Input Face Scan Image ]
           │
           ▼
┌──────────────────────────────────────────────┐
│  PART 1: Face Engine (Detection & Encoding)  │
│  - Face bounding box localization            │
│  - 512-D L2-normalized vector embedding      │
│  - Deterministic Biometric Fingerprint (SHA) │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│  PART 2: Web / Social Media Visual Search    │
│  - Reverse visual search / social query      │
│  - Finds genuine matching post (X, LinkedIn) │
│  - Extracts URL, author, text & media hash   │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│  PART 3: Blockchain Record Anchoring         │
│  - Generates composite Keccak-256 record hash│
│  - Deploys/calls FaceVerificationRegistry    │
│  - Mines transaction into immutable block    │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│  PART 4: On-Chain Verification & Tamper Test │
│  - Queries on-chain state by record hash     │
│  - Proves data equality against chain record │
│  - Rejects forged/altered post content       │
└──────────────────────────────────────────────┘
```

---

## 📂 Module Breakdown

The codebase is organized into isolated, reusable packages:

```
HH-task3/
├── main.py                          # Root CLI entrypoint
├── requirements.txt                 # Dependencies (deepface, tf-keras, langgraph, etc.)
├── .env.example                     # Environment template
├── .gitignore                       # Standard version control ignores
├── README.md                        # Documentation & submission guide
│
├── src/                             # Core modular source packages
│   ├── __init__.py
│   ├── face_detection/              # SEGMENT 1: Face Detection & Encoding
│   │   ├── __init__.py
│   │   └── detector.py              # DeepFace MTCNN + Facenet512 + 30% padding crop
│   │
│   ├── web_search/                  # SEGMENT 2: Web & Social Media Reverse Search
│   │   ├── __init__.py
│   │   └── searcher.py              # Reverse visual search + metadata & content fingerprinting
│   │
│   ├── blockchain/                  # SEGMENT 3: Blockchain Anchoring & Verification
│   │   ├── __init__.py
│   │   └── verifier.py              # Composite Keccak-256 fingerprinting & on-chain verification
│   │
│   └── pipeline/                    # SEGMENT 4: LangGraph Pipeline Orchestrator (Glue Script)
│       ├── __init__.py
│       └── orchestrator.py          # StateGraph (face_detect -> web_search -> blockchain_verify)
│
├── contracts/                       # Solidity smart contract & compiled ABI
│   ├── FaceVerificationRegistry.sol
│   └── FaceVerificationRegistry.json
│
├── samples/                         # Sample portrait images for demonstration
│   ├── README.md
│   └── sample_faces/
│       └── sample_person.jpg
│
├── tests/                           # Modular test suite
│   ├── test_face_detection.py
│   ├── test_web_search.py
│   ├── test_blockchain.py
│   └── test_pipeline.py
│
└── output/                          # Persisted verification receipts & crops
```

---

### Part 1: Face Detection & Encoding
- **Module**: `src/face_engine/`
- **Responsibilities**:
  - Localizes faces within any input image and computes normalized bounding box coordinates.
  - Crops and pre-processes the face to standardized 160×160 RGB tensors.
  - Passes features through a deep convolutional feature extractor producing an affine-invariant **512-dimensional normalized vector embedding**.
  - Derives a deterministic cryptographic **Biometric Hash (SHA-256)** for tamper-proof registry on-chain.

### Part 2: Web & Social Media Search
- **Module**: `src/social_search/`
- **Responsibilities**:
  - Executes a **genuine reverse visual search** using the face crop to find matching public posts across social networks (e.g. X/Twitter, LinkedIn, Instagram, Reddit, GitHub).
  - Supports multiple backends:
    1. **SerpApi (Google Lens engine)**: For API-powered reverse visual lookup.
    2. **Scripted Search Engine**: Automated query execution targeting social media platforms without requiring paid API keys.
  - Parses the discovered post to extract canonical URL, author, platform, post text snippet, and media URLs.
  - Computes a cryptographic SHA-256 fingerprint over the post's content and media.

### Part 3: Blockchain Verification
- **Module**: `src/blockchain_verifier/`
- **Responsibilities**:
  - Synthesizes a composite 32-byte cryptographic record:  
    $$\text{RecordHash} = \text{Keccak256}(\text{FaceHash} \parallel \text{PostURL} \parallel \text{PostContentHash} \parallel \text{Timestamp})$$
  - Anchors this record to the blockchain via `FaceVerificationRegistry`.
  - Implements **re-verification**: queries the on-chain immutable state, recomputes the composite hash from candidate data, and asserts 100% equivalence.
  - Flags any tampering if even a single character of the post URL, caption, or biometric hash is modified.

### Part 4: Glue Script
- **Module**: `run_pipeline.py` & `src/pipeline/`
- **Responsibilities**:
  - Glues all components into a single seamless CLI pipeline.
  - Runs face scan → social discovery → blockchain anchor → tamper verification.
  - Renders a color-coded terminal report with timestamps, block numbers, transaction hashes, and gas metrics.
  - Exports a persistent machine-readable audit receipt to `output/verification_receipt_<id>.json`.

---

## ⛓️ Which Blockchain is Used?

This project supports **Dual-Mode Blockchain Operation**:

1. **In-Process Verifiable Cryptographic Blockchain (`simulated` mode, Default)**:
   - Built directly into the client with real SHA-256 block hashing, parent block pointers, merkle transactions, state transitions, and cryptographic verification.
   - **Why this is ideal for evaluation**: Runs offline with zero network latency, zero gas/faucet dependencies, and 100% reliability during screen recordings.
2. **EVM Testnets / Local RPC (`sepolia`, `polygon_amoy`, or `local_rpc`)**:
   - Deploys and interacts with the included Solidity smart contract [`contracts/FaceVerificationRegistry.sol`](file:///d:/Projects/HH-task3/contracts/FaceVerificationRegistry.sol).
   - Configurable via `.env` by providing an RPC URL and private key.

---

## 📜 Smart Contract Architecture

The [`FaceVerificationRegistry.sol`](file:///d:/Projects/HH-task3/contracts/FaceVerificationRegistry.sol) contract defines:

```solidity
struct VerificationRecord {
    bytes32 recordHash;        // Keccak-256 composite hash
    bytes32 faceHash;          // Biometric face hash
    bytes32 postContentHash;   // Discovered post content hash
    string postUrl;            // Public social post URL
    string platform;           // E.g. "X (Twitter)", "LinkedIn"
    uint256 timestamp;         // Block timestamp when anchored
    address submitter;         // Wallet address
    bool exists;
}
```

Key functions:
- `anchorRecord(...)`: Anchors a record and emits `RecordAnchored`.
- `verifyRecord(bytes32 recordHash)`: Returns immutable on-chain record data.
- `isRecordValid(bytes32 recordHash)`: Constant-time membership check.

---

## 💻 Installation & Setup

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd HH-task3
```

### 2. Set up Python environment
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment (Optional)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(Default settings run completely out-of-the-box with zero configuration required!)*

---

## ⚡ How to Run

### 1. Live Camera Face Scan (Recommended for Screen Recording)
Launch the pipeline with your webcam. An alignment reticle window opens with instructions:
- Press **[SPACE]** to capture the face scan.
- Press **[Q]** to cancel.
```bash
python main.py --camera
```
*(Optionally append `--demo-tamper` to also demonstrate live cryptographic tamper-evidence).*

### 2. Run with Sample Face Image
Run the pipeline using the included sample face scan:
```bash
python main.py samples/sample_faces/sample_person.jpg
```
Or specify any custom face image path:
```bash
python main.py path/to/your_face_image.jpg
```

### 3. Demonstrate Tamper-Evidence
Run with the `--demo-tamper` flag to prove how the blockchain immediately flags and rejects spoofed or altered social media data:
```bash
python main.py samples/sample_faces/sample_person.jpg --demo-tamper
```

### 4. Run Individual Modules Standalone

Each segment can be inspected and executed independently:

#### Segment 1: Camera Capture & Face Detection
```bash
# Interactive camera capture with live reticle guide
python -m src.face_detection.camera

# Face detection & 512-D embedding on an image
python -m src.face_detection.detector samples/sample_faces/sample_person.jpg
```

#### Segment 2: Web & Social Media Visual Search
```bash
python -m src.web_search.searcher output/face_crop.jpg
```

#### Segment 3: Blockchain Verification & Tamper Detection
```bash
python -m src.blockchain.verifier
```

---

## 🧪 Running Automated Tests

Run the full test suite using `pytest`:
```bash
pytest tests/ -v
```

All 4 test suites will execute:
- `tests/test_face_engine.py`: Bounding box detection, 512-D embedding generation, biometric hashing.
- `tests/test_social_search.py`: Post extraction, OpenGraph parsing, content fingerprinting.
- `tests/test_blockchain.py`: Record anchoring, chain validation, cryptographic tamper detection.
- `tests/test_pipeline.py`: Full end-to-end integration test.

---

## ⚠️ Known Limitations & Technical Gotchas

- **`tf-keras` Gotcha**: Current TensorFlow (`>=2.21`) requires `pip install tf-keras` alongside `deepface`, or detector backends (like RetinaFace/MTCNN) throw a `ModuleNotFoundError` at import due to Keras 3 compatibility changes. This is pre-configured in `requirements.txt`.
- **Detector Backend (`mtcnn` vs `retinaface`)**: Using `mtcnn` as the default detector backend gives a superior speed/accuracy balance for live demonstrations. `retinaface` offers higher accuracy for difficult angles but is noticeably slower on CPU.
- **Embedding Representation (`Facenet512`)**: Produces a standardized 512-dimensional continuous biometric embedding representation, ideal for cryptographic hashing and vector indexing.
- **Contextual 30% Padding on Face Crop**: The face cropping step automatically adds 30% context padding around the detected bounding box to preserve forehead, chin, and hair features, ensuring reverse image search engines receive realistic visual context rather than a tight, cropped square.
- **Deterministic Pipeline Backbone (LangGraph)**: The orchestration pipeline leverages LangGraph's `StateGraph` for predictable, stateful node progression (`face_detect -> web_search -> blockchain_verify`). CrewAI is scoped exclusively for agentic judgment (e.g., selecting the most relevant candidate among ambiguous multi-match search results).
- **Social Platform Rate Limits**: Automated scraping of public social media pages (X/Twitter, LinkedIn) is subject to rate-limiting by platforms without authenticated API keys. The pipeline gracefully falls back to verified public search snippets when direct scraping is restricted.
- **Public Network Gas**: When using public EVM testnets (Sepolia / Polygon Amoy) instead of the simulated chain, transaction confirmation depends on network congestion and requires testnet faucet tokens.

---

## 🎥 Submission & Video Recording Checklist

- [x] Full source code organized in modular directories
- [x] Part 1: Face detection & encoding implemented
- [x] Part 2: Genuine web/social search implemented
- [x] Part 3: Blockchain anchoring and verification implemented
- [x] Part 4: Glue script (`run_pipeline.py`) tying all parts together
- [x] Comprehensive README with setup, architecture, and limitations
- [x] Automated test suite passing
- [ ] Screen recording showing:
  1. Terminal launching `python run_pipeline.py --input samples/sample_faces/sample_person.jpg`
  2. Face detection bounding box & 512-D biometric hash output
  3. Real social media post discovery and metadata extraction
  4. Blockchain anchoring (transaction hash & block number)
  5. Successful on-chain tamper-evidence verification
