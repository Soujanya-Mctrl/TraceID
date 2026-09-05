# FaceScan-Blockchain-Verification 🛡️🔗

> **HH Goa 2026 Shortlisting Task 3**: Face Identification & Blockchain Verification  
> An end-to-end, privacy-preserving pipeline that captures or accepts a human face scan, discovers matching public content across the web & social platforms through genuine reverse visual search, and cryptographically anchors & verifies that discovered record on an immutable blockchain ledger.

---

## 📋 Table of Contents
- [System Overview](#-system-overview)
- [Pipeline Architecture](#-pipeline-architecture)
- [Project Directory Structure](#-project-directory-structure)
- [Detailed Architecture & Privacy Design](#-detailed-architecture--privacy-design)
- [Quick Start](#-quick-start)
- [How to Run](#-how-to-run)
  - [1. Full Pipeline Execution](#1-full-pipeline-execution)
  - [2. Live Webcam Face Scan](#2-live-webcam-face-scan)
  - [3. Demonstrate Cryptographic Tamper-Evidence](#3-demonstrate-cryptographic-tamper-evidence)
  - [4. Deploying to Polygon Amoy Testnet](#4-deploying-to-polygon-amoy-testnet)
  - [5. Standalone Module Execution](#5-standalone-module-execution)
- [Running Automated Tests](#-running-automated-tests)
- [Which Blockchain is Used?](#-which-blockchain-is-used)
- [Smart Contract Architecture](#-smart-contract-architecture)
- [Known Limitations & Technical Considerations](#-known-limitations--technical-considerations)
- [Submission & Video Recording Checklist](#-submission--video-recording-checklist)

---

## 🌟 System Overview

This project implements an authentic, production-grade identity attestation pipeline linking deep computer vision, real-world reverse image search, and immutable smart contracts:

1. **Precision Biometrics & Quality Gate**: Detects faces via MTCNN, measures eye landmarks, evaluates Laplacian blur, anatomical roll tilt, and yaw proxy, generating a continuous 512-dimensional Facenet vector embedding.
2. **Real Web Visual Search**: Discovers live matching posts across X, LinkedIn, Instagram, Reddit, and Pinterest using Google Lens via SerpAPI's optimized 2-step Image Upload API.
3. **Face Verification Layer**: Downloads candidate images and computes cosine similarity against every face detected in candidate photos (handles group photos). Rejects hallucinations with a threshold of $\ge 0.55$.
4. **Privacy-Preserving Blockchain Anchoring**: Strictly follows data minimization. **Zero face embeddings and zero raw image bytes touch the blockchain.** Only a canonicalized, deterministic Keccak-256 metadata hash is anchored to the smart contract (`contracts/PostVerifier.sol`).
5. **Stateful DAG Orchestration**: Built with LangGraph, compiling clean state progression with persistent machine-readable audit receipts.

---

## 🚀 Pipeline Architecture

```
[ Input Face Scan: Webcam or Image File ]
                   │
                   ▼
┌────────────────────────────────────────────────────────┐
│  STAGE 1: Face Engine & Biometric Quality Assurance    │
│  - MTCNN bounding box localization & landmark tracking │
│  - Quality Filter: Blur (>=60), Roll (<=25°), Yaw prox │
│  - 512-D L2-normalized vector embedding (Facenet512)   │
│  - Contextual 30% padded crop (output/face_crop.jpg)   │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│  STAGE 2: Web / Social Media Search & Verification     │
│  - SerpAPI 2-step local image upload (POST /image)     │
│  - Google Lens reverse visual search (type=all, 1 cred)│
│  - Downloads candidate images & runs in-image face net │
│  - Group photo check: verifies all faces via cosine sim│
│  - Filters & ranks: Verified Social > Verified Web     │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│  STAGE 3: Privacy-Preserving Blockchain Anchoring      │
│  - Canonical post metadata dict (sorted-key JSON)      │
│  - Deterministic Keccak-256 32-byte hash computation   │
│  - Anchors dataHash to PostVerifier.sol (Polygon Amoy) │
│  - Emits on-chain transaction & records block number   │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│  STAGE 4: On-Chain Re-Verification & Tamper Test       │
│  - Reads state back from contract: verifyRecord(hash)  │
│  - Confirms exists == true and valid block timestamp   │
│  - Demonstrates tamper detection if payload is altered │
│  - Exports audit receipt (output/verification_receipt) │
└────────────────────────────────────────────────────────┘
```

---

## 📂 Project Directory Structure

```
HH-task3/
├── main.py                          # Unified CLI entrypoint with camera & tamper flags
├── pipeline.py                      # Root LangGraph pipeline runner
├── serp_search.py                   # Standalone SerpAPI Google Lens visual search CLI
├── web_search.py                    # Standalone Web Search & verification CLI
├── chain.py                         # Privacy-preserving blockchain anchoring & verification
├── requirements.txt                 # Project dependencies
├── contract_abi.json                # Pre-compiled ABI for PostVerifier contract
├── .env.example                     # Environment template
├── .gitignore                       # Version control rules
├── README.md                        # Project documentation
├── ARCHITECTURE.md                  # Comprehensive technical specification & diagrams
│
├── contracts/                       # Smart contracts
│   ├── PostVerifier.sol             # Privacy-preserving metadata anchoring contract
│   ├── FaceVerificationRegistry.sol # Extended registry contract
│   └── FaceVerificationRegistry.json# Pre-compiled registry ABI
│
├── scripts/                         # Automation & deployment scripts
│   └── deploy.py                    # Compiles & deploys PostVerifier.sol via py-solc-x
│
├── src/                             # Core modular packages
│   ├── face_detection/              # SEGMENT 1: Face Detection, Quality & Embeddings
│   │   ├── camera.py                # 2-tier live webcam capture (Haar tracking + MTCNN)
│   │   ├── detector.py              # MTCNN detector, 30% padding crop, Facenet512 encoder
│   │   └── quality.py               # Blur, anatomical roll angle, yaw proxy scoring
│   │
│   ├── web_search/                  # SEGMENT 2: Web & Social Visual Search
│   │   ├── serp_search.py           # SerpAPI Google Lens local image upload & parsing
│   │   └── searcher.py              # Google Vision / Fallback & in-image face verification
│   │
│   ├── blockchain/                  # SEGMENT 3: Blockchain Anchoring & Verification
│   │   └── verifier.py              # Cryptographic verification & in-process ledger
│   │
│   └── pipeline/                    # SEGMENT 4: Orchestrator
│       └── orchestrator.py          # LangGraph StateGraph (face -> search -> blockchain)
│
├── samples/                         # Sample portrait images for demonstration
│   ├── README.md
│   └── sample_faces/
│       └── sample_person.jpg        # Standard test image
│
├── tests/                           # Comprehensive test suite (19 unit & integration tests)
│   ├── test_face_detection.py       # Detection, landmark math, quality gate tests
│   ├── test_web_search.py           # Search mapping, SerpAPI upload, verification tests
│   ├── test_blockchain.py           # Keccak hashing, tamper detection tests
│   └── test_pipeline.py             # Full LangGraph execution test
│
└── output/                          # Generated artifacts
    ├── face_crop.jpg                # 30% padded crop used for reverse search
    └── verification_receipt.json    # Machine-readable on-chain audit receipt
```

---

## 🔒 Detailed Architecture & Privacy Design

For an exhaustive architectural deep-dive, mathematical quality equations, and security threat models, see:
👉 **[`ARCHITECTURE.md`](ARCHITECTURE.md)**

### The Non-Negotiable Privacy Rule:
- **What goes on-chain**: Only the 32-byte Keccak-256 hash of canonical post metadata (`platform`, `page_url`, `image_url`, `page_title`, `verified`, `similarity`).
- **What NEVER goes on-chain**: Zero face embeddings, zero biometric templates, and zero raw image bytes. Biometric data remains strictly in transient local memory during execution.

---

## ⚡ Quick Start

### 1. Clone & Set Up Environment
```bash
git clone <repo-url>
cd HH-task3

# Create & activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Key settings in `.env`:
```env
# Visual Search Backend: "serp" (SerpAPI Google Lens) or "vision" (Google Cloud Vision)
SEARCH_BACKEND=serp
SERPAPI_API_KEY=your_serpapi_key_here

# Blockchain Network: "simulated" (instant offline) or "polygon_amoy"
AMOY_RPC_URL=https://polygon-amoy.drpc.org
PRIVATE_KEY=your_testnet_private_key
CONTRACT_ADDRESS=your_deployed_contract_address
```
*(Out of the box, default settings run reliably with zero external blockchain setup required!)*

---

## 🎮 How to Run

### 1. Full Pipeline Execution
Run the end-to-end LangGraph pipeline on any image:
```bash
python pipeline.py samples/sample_faces/sample_person.jpg
```
Or via `main.py`:
```bash
python main.py samples/sample_faces/sample_person.jpg
```

**Expected Terminal Output**:
```text
======================================================================
HH Goa 2026: Face Identification & Blockchain Verification Pipeline
Mode: Image File (samples/sample_faces/sample_person.jpg)
======================================================================

[Stage 1: Face Detection] Detecting & scoring face quality...
  Confidence: 1.0
  Saved 30% padded crop to: output/face_crop.jpg

[Stage 2: Web Search] Harvesting candidates via [SERP] & verifying against face embedding...
  Discovered Post:    https://in.pinterest.com/sureshdx606/funny-short-clips/
  Face Match Status:  VERIFIED
  Cosine Similarity:  0.9603
  Audit Note:         VERIFIED: Face match confirmed via cosine similarity (0.960)

[Stage 3: Blockchain] Anchoring post metadata hash & re-verifying...
  Anchored on Block #1
  Transaction Hash: 0xdea3abf380306e51d95f4fca95f3aa1305b8c7a50898134a2756641e14ee29c2
  Record Hash: 0x7a302956afa326ffcb876e3fd5b4947e6004b2135f58fe0dfb3bc4ba40286fcb
  Re-verification Status: VERIFIED: Discovered data matches immutable on-chain record exactly.
  Persisted verification receipt to: output/verification_receipt.json
```

---

### 2. Live Webcam Face Scan
Capture a real-time face scan using your computer's webcam:
```bash
python main.py --camera
```
- **Real-time feedback**: A live HUD window displays an alignment guide with a real-time face box.
- **Stability gate**: Keeps tracking until the face is stable for 20 frames before capturing.
- **Controls**: Press **[SPACE]** to capture immediately, or **[Q]** to cancel.

---

### 3. Demonstrate Cryptographic Tamper-Evidence
Demonstrate how the blockchain instantly catches and rejects altered or spoofed post data:
```bash
python main.py samples/sample_faces/sample_person.jpg --demo-tamper
```
**Tamper Demonstration Output**:
```text
[Tamper Demonstration]: Testing forged post URL against blockchain...
  Forged URL Result: TAMPER DETECTED: Candidate hash 0x4b8e22... != On-chain hash 0x39da3e...
  Tamper-evidence successfully proven!
```

---

### 4. Deploying to Polygon Amoy Testnet

To deploy the smart contract to live Polygon Amoy:
1. Ensure your `.env` contains:
   ```env
   AMOY_RPC_URL=https://polygon-amoy.drpc.org
   PRIVATE_KEY=your_testnet_private_key
   ```
   *(Ensure your testnet wallet has free testnet MATIC from the Polygon Amoy faucet)*
2. Run the deployment script:
   ```bash
   python scripts/deploy.py
   ```
   This compiles `contracts/PostVerifier.sol` using `py-solc-x`, deploys the contract, writes `contract_abi.json`, and outputs:
   ```text
   Contract deployed successfully at: 0x1234567890abcdef...
   Set CONTRACT_ADDRESS=0x1234567890abcdef... in your .env
   ```
3. Add the printed address to `CONTRACT_ADDRESS` in `.env`.
4. Now all runs of `pipeline.py` will broadcast live transactions directly to Polygon Amoy!

---

### 5. Standalone Module Execution

Each pipeline component can be tested independently:

#### Test SerpAPI Reverse Search:
```bash
python serp_search.py output/face_crop.jpg
```

#### Test Blockchain Hashing & Payload Canonicalization:
```bash
python chain.py
```

#### Test Face Detection & 512-D Embedding:
```bash
python -m src.face_detection.detector samples/sample_faces/sample_person.jpg
```

#### Test Camera HUD:
```bash
python -m src.face_detection.camera
```

---

## 🧪 Running Automated Tests

Run the full pytest suite:
```bash
pytest tests/ -v
```

**Test Suite Coverage (19 Passed)**:
- `tests/test_face_detection.py`: MTCNN detection, 30% padding crop, camera HUD, anatomical eye roll tilt math, yaw proxy symmetry, quality scoring composite gate.
- `tests/test_web_search.py`: Social domain detection, deterministic fingerprinting, OpenGraph extraction, orthogonal/identical cosine similarity, mock SerpAPI upload, Google Lens candidate mapping, dependency-injected search function.
- `tests/test_blockchain.py`: Keccak-256 hash determinism, authentic record anchoring & verification, cryptographic tamper detection.
- `tests/test_pipeline.py`: Full LangGraph DAG end-to-end integration test.

---

## ⛓️ Which Blockchain is Used?

This architecture features **Dual-Mode Blockchain Operation**:
1. **Polygon Amoy EVM Testnet**: Interacts with the deployed Solidity smart contract [`contracts/PostVerifier.sol`](contracts/PostVerifier.sol) via Web3.py.
2. **In-Process Verifiable Cryptographic Ledger (`simulated` mode, Default)**: A deterministic cryptographic ledger built into `src/blockchain/verifier.py` with real SHA-256/SHA3 block hashing, parent hash linking, and state transitions. **Enables 100% reliable evaluation with zero network latency, zero faucet dependency, and complete offline auditability.**

---

## ⚠️ Known Limitations & Technical Considerations

1. **Near-Duplicate vs Closed Face-Recognition Index**:
   Google Lens/SerpAPI is a public reverse visual search index, not a mass-surveillance facial recognition database (like Clearview AI). It excels at finding images the person has actually posted online or images that visually match public photos, rather than arbitrary private candid shots.
2. **CDN Hotlink Restrictions**:
   Some social platforms rate-limit or block external image scraping without browser sessions. The verification layer gracefully flags un-downloadable images as unverified candidates rather than crashing the pipeline.
3. **500KB Upload Limit on SerpAPI**:
   SerpAPI's local image upload endpoint enforces a 500KB cap. `src/web_search/serp_search.py` automatically compresses and downsamples large webcam frames before transmission.
4. **Duplicate Record Rejection**:
   `PostVerifier.sol` strictly enforces `require(!records[dataHash].exists)`. Running the exact same payload twice on a live blockchain will revert on the second run to prevent timestamp spoofing.

---

## 🎥 Submission & Video Recording Checklist

- [x] Full source code organized into clean, modular packages
- [x] Part 1: Face detection, landmark quality scoring & 512-D embedding implemented
- [x] Part 2: Real reverse image search (SerpAPI Google Lens) & face verification implemented
- [x] Part 3: Privacy-preserving blockchain anchoring (`contracts/PostVerifier.sol` & `chain.py`) implemented
- [x] Part 4: LangGraph orchestrator (`pipeline.py`) tying all parts together
- [x] Comprehensive architectural specification in [`ARCHITECTURE.md`](ARCHITECTURE.md)
- [x] Automated test suite passing (19/19 tests)
- [x] Screen recording demonstrations supported:
  1. Live webcam scan: `python main.py --camera`
  2. Sample face pipeline run: `python pipeline.py samples/sample_faces/sample_person.jpg`
  3. Tamper-evidence proof: `python main.py samples/sample_faces/sample_person.jpg --demo-tamper`
  4. Unit test execution: `pytest tests/ -v`
