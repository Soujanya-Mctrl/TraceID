# TraceID 🛡️🔗

### Privacy-Preserving Facial Biometrics, Web Entity Resolution & Immutable Blockchain Verification

> **TraceID** is an end-to-end, privacy-preserving pipeline developed for **HH Goa 2026 Shortlisting Task 3 (Face Identification & Blockchain Verification)**. It captures or accepts a human face scan, discovers matching public content across the web & social platforms through genuine reverse visual search and entity resolution, and cryptographically anchors & verifies that discovered record on a live immutable blockchain ledger.

[![Watch Demo Video](https://img.shields.io/badge/📺_Demo_Video-Watch_on_Google_Drive-blue?style=for-the-badge&logo=google-drive)](https://drive.google.com/file/d/1BCKwoHe769dVeVuzDKDuARDbxfiuggeA/view?usp=sharing)

---

## 📋 Table of Contents
- [📺 Demo Video](#-demo-video)
- [System Overview](#-system-overview)
- [Pipeline Architecture](#-pipeline-architecture)
- [Project Directory Structure](#-project-directory-structure)
- [Detailed Architecture & Privacy Design](#-detailed-architecture--privacy-design)
- [Quick Start](#-quick-start)
- [How to Run](#-how-to-run)
  - [1. Full Pipeline Execution on Image Files](#1-full-cli-pipeline-execution)
  - [2. Live Webcam Face Scan](#2-live-webcam-face-scan)
  - [3. Interactive Web Application (FastAPI + React)](#3-interactive-web-application-fastapi--react-)
  - [4. On-Chain Authenticity & Integrity Audit](#4-on-chain-authenticity--integrity-audit)
  - [5. Standalone Module Execution](#5-standalone-module-execution)
- [Running Automated Tests](#-running-automated-tests)
- [Which Blockchain is Used?](#-which-blockchain-is-used)
- [Smart Contract Architecture](#-smart-contract-architecture)
- [Known Limitations & Technical Considerations](#-known-limitations--technical-considerations)
- [Submission & Video Recording Checklist](#-submission--video-recording-checklist)

---

## 📺 Demo Video

A comprehensive video walkthrough demonstrating the full end-to-end pipeline in action:

🎬 **[Watch the Live Demo Video on Google Drive](https://drive.google.com/file/d/1BCKwoHe769dVeVuzDKDuARDbxfiuggeA/view?usp=sharing)**

**Demonstration highlights**:
- Real-time webcam face scan with bounding box HUD and stability gating.
- Real web reverse search via Google Lens (SerpAPI) & Wikipedia entity resolution.
- Downstream in-image face verification via cosine similarity.
- Live Polygon Amoy EIP-1559 transaction anchoring (`PostVerifier.sol`).
- On-chain authenticity verification proving zero fraud and immutable record integrity.
- Full-stack interactive web application (FastAPI + React).

---

## 🌟 System Overview

This project implements an authentic, production-grade identity attestation pipeline linking deep computer vision, real-world reverse image search with entity resolution, and immutable smart contracts:

1. **Precision Biometrics & Quality Gate**: Detects faces via MTCNN, measures eye landmarks, evaluates Laplacian blur ($\ge 60$), anatomical roll tilt ($\le 25^\circ$), and horizontal yaw proxy ($\le 0.45$), generating an affine-invariant 512-dimensional Facenet vector embedding.
2. **Real Web Visual Search**: Discovers live matching posts and pages across the web using Google Lens via SerpAPI's optimized 2-step Image Upload API.
3. **Entity Resolution & Smart Re-Ranking**: Eliminates random short-form video reels, meme boards (`/pin/`), and YouTube shorts. Resolves the person's identity via Wikipedia REST API and redirects to canonical identity profiles (Wikipedia, IMDb, Forbes, or clean profile roots).
4. **Face Verification Layer**: Downloads candidate images and computes cosine similarity against every face detected in candidate photos (handles group photos). Rejects hallucinations with a threshold of $\ge 0.55$.
5. **Privacy-Preserving Blockchain Anchoring (100% Live)**: Strictly follows data minimization. **Zero face embeddings and zero raw image bytes touch the blockchain.** Only a canonicalized, deterministic Keccak-256 metadata hash is anchored to the live smart contract (`contracts/PostVerifier.sol`) on **Polygon Amoy Testnet** (`0xB066F1C56c530189876c4c538D089997Fb5C4398`).
6. **EIP-1559 Dynamic Fee Optimization & Zero-Gas Cache**: Slashes transaction gas costs by 87% using Type-2 EIP-1559 fee parameters (`~0.0026 POL`). Pre-checks on-chain state so repeated evaluations cost **0 gas**.
7. **Stateful DAG Orchestration**: Built with LangGraph, compiling clean state progression with persistent machine-readable audit receipts.

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
│  STAGE 2: Web Search, Entity Resolution & Re-Ranking   │
│  - SerpAPI 2-step local image upload (POST /image)     │
│  - Google Lens visual search + related content query   │
│  - Wikipedia REST API Entity Resolver (name/bio/photo) │
│  - Multi-Factor Re-Ranking: Penalize reels (-50 pts),  │
│    boost canonical profiles (+50 pts) & biometrics     │
│  - Downloads candidate images & runs in-image face net │
│  - Group photo check: verifies all faces via cosine sim│
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│  STAGE 3: Privacy-Preserving Blockchain Anchoring      │
│  - Canonical post metadata dict (sorted-key JSON)      │
│  - Deterministic Keccak-256 32-byte hash computation   │
│  - Anchors dataHash to PostVerifier.sol (Polygon Amoy) │
│  - EIP-1559 Type-2 tx (25 Gwei priority, 76,000 gas)   │
│  - Emits on-chain transaction & records block number   │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│  STAGE 4: On-Chain Re-Verification & Authenticity Audit│
│  - Reads state back from contract: verifyRecord(hash)  │
│  - Confirms exists == true and valid block timestamp   │
│  - Confirms submitter address matches testnet wallet   │
│  - Exports audit receipt (output/verification_receipt) │
│  - Proves NO FRAUD DETECTED with live Polygonscan link │
└────────────────────────────────────────────────────────┘
```

---

## 📂 Project Directory Structure

```
TraceID/
├── requirements.txt                 # Project dependencies
├── .env.example                     # Environment template
├── .gitignore                       # Version control rules
├── README.md                        # Project documentation
├── ARCHITECTURE.md                  # Comprehensive technical specification & diagrams
│
├── web/                             # Full-Stack Web Application
│   ├── server/                      # FastAPI Backend (REST endpoints, static mounting & pipeline runner)
│   │   ├── server.py
│   │   └── __init__.py
│   └── client/                      # Modern React Frontend (Vite, CSS Modules, Lucide icons)
│       ├── src/                     # React components, webcam HUD, stepper & styles
│       ├── dist/                    # Production distribution bundle
│       └── package.json             # Frontend dependencies
│
├── contracts/                       # Smart contracts & pre-compiled ABIs
│   ├── PostVerifier.sol             # Privacy-preserving metadata anchoring contract
│   ├── PostVerifier.json            # Pre-compiled ABI for PostVerifier contract
│   ├── FaceVerificationRegistry.sol # Extended registry contract
│   └── FaceVerificationRegistry.json# Pre-compiled registry ABI
│
├── scripts/                         # Automation & deployment scripts
│   └── deploy.py                    # Compiles & deploys PostVerifier.sol via py-solc-x
│
├── src/                             # Core modular package
│   ├── __init__.py                  # Package exports
│   ├── __main__.py                  # Enables `python -m src` CLI execution
│   ├── main.py                      # Unified CLI entrypoint (pipeline, camera HUD, web server, SerpAPI)
│   │
│   ├── face_detection/              # SEGMENT 1: Face Detection, Quality & Embeddings
│   │   ├── camera.py                # 2-tier live webcam capture (Haar tracking + MTCNN)
│   │   ├── detector.py              # MTCNN detector, 30% padding crop, Facenet512 encoder
│   │   └── quality.py               # Blur, anatomical roll angle, yaw proxy scoring
│   │
│   ├── web_search/                  # SEGMENT 2: Web & Social Visual Search
│   │   ├── entity_resolver.py       # Wikipedia REST API entity resolver & URL classifier
│   │   ├── serp_search.py           # SerpAPI Google Lens local image upload & harvesting
│   │   └── searcher.py              # Multi-factor re-ranking & in-image face verification
│   │
│   ├── blockchain/                  # SEGMENT 3: Blockchain Anchoring & Verification
│   │   ├── chain.py                 # Polygon Amoy EVM Web3 smart contract interaction & EIP-1559 gas
│   │   └── verifier.py              # Cryptographic on-chain verification helpers
│   │
│   └── pipeline/                    # SEGMENT 4: Orchestrator
│       └── orchestrator.py          # LangGraph StateGraph (face -> search -> blockchain)
│
├── samples/                         # Sample portrait images for demonstration
│   ├── README.md
│   └── sample_faces/
│       ├── sample_person.jpg        # Standard test image (CarryMinati / Ajey Nagar)
│       ├── sample.jpg               # High-profile test image (Kevin Hart)
│       └── images.jpg               # Actor test image (Kunal Khemu)
│
├── tests/                           # Comprehensive test suite (22 unit & integration tests)
│   ├── test_face_detection.py       # Detection, landmark math, quality gate tests
│   ├── test_web_search.py           # Search mapping, entity resolution, re-ranking tests
│   ├── test_blockchain.py           # Keccak hashing, live on-chain anchoring & tamper tests
│   └── test_pipeline.py             # Full LangGraph execution integration test
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
git clone https://github.com/Soujanya-Mctrl/TraceID.git
cd TraceID

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
Copy `.env.example` to `.env` (or use the pre-configured `.env`):
```bash
cp .env.example .env
```
Key settings in `.env`:
```env
# Visual Search Backend: "serp" (SerpAPI Google Lens)
SEARCH_BACKEND=serp
SERPAPI_API_KEY=your_serpapi_key_here

# Blockchain Network: Live Polygon Amoy Testnet (Chain ID 80002)
AMOY_RPC_URL=https://polygon-amoy.drpc.org
BLOCKCHAIN_RPC_URL=https://polygon-amoy.drpc.org
CONTRACT_ADDRESS=0xB066F1C56c530189876c4c538D089997Fb5C4398
PRIVATE_KEY=your_testnet_private_key
```

---

## 🎮 How to Run

### 1. Full CLI Pipeline Execution
Run the end-to-end LangGraph pipeline on any image:
```bash
python -m src samples/sample_faces/sample_person.jpg
# or on another sample:
python -m src samples/sample_faces/sample.jpg
```

**Live Verified Terminal Output**:
```text
======================================================================
TraceID: Face Identification & Blockchain Verification Pipeline
Mode: Image File (samples/sample_faces/sample.jpg)
======================================================================

[Stage 1: Face Detection] Detecting and encoding face with DeepFace...
  Confidence: 1.0
  Saved 30% padded crop to: output\face_crop.jpg

[Stage 2: Web Search] Harvesting candidates via [SERP] & verifying against face embedding...
  Identified Person:  Kevin Hart (American comedian and actor (born 1979))
  Canonical Page:     https://en.wikipedia.org/wiki/Kevin_Hart
  Platform:           Official Identity / Wikipedia | Author: Kevin Hart
  Face Match Status:  VERIFIED
  Cosine Similarity:  0.9886
  Re-Rank Score:      194.77
  Audit Note:         VERIFIED: Face match confirmed via cosine similarity (0.989)
  Content Fingerprint:0xcd29430942a71f50ed4e14155d5b2c15ce9e2e7a8f5a80833c2a15921a6bded2

[Stage 3 & 4: Blockchain] Anchoring post metadata to live Polygon Amoy blockchain...
  Live Network:       Polygon Amoy Testnet (Chain ID 80002)
  Contract Address:   0xB066F1C56c530189876c4c538D089997Fb5C4398
  Anchored on Block:  #46982651
  Transaction Hash:   0xf272922d3f096d07358d69dd980afda03369bbd2647674d6e4c84339c5bd7aed
  Record Hash:        0xe6c0970c26a5df29ccde1dbff16a6a3ac563cc283beb340d19a07d3995375178
  Re-verification:    VERIFIED: Immutable on-chain record matches data
  Polygonscan Link:   https://amoy.polygonscan.com/tx/0xf272922d3f096d07358d69dd980afda03369bbd2647674d6e4c84339c5bd7aed
  Persisted verification receipt to: output\verification_receipt.json

======================================================================
PIPELINE COMPLETED SUCCESSFULLY [OK]
  Captured Scan:       samples/sample_faces/sample.jpg
  Identified Identity: Kevin Hart (American comedian and actor (born 1979))
  Canonical Page URL:  https://en.wikipedia.org/wiki/Kevin_Hart
  Face Match Status:   VERIFIED
  Cosine Similarity:   0.9886
  Re-Rank Score:       194.77
  Blockchain Block:    #46982651
  Transaction Hash:    0xf272922d3f096d07358d69dd980afda03369bbd2647674d6e4c84339c5bd7aed
  Polygonscan Link:    https://amoy.polygonscan.com/tx/0xf272922d3f096d07358d69dd980afda03369bbd2647674d6e4c84339c5bd7aed
  On-Chain Verified:   True
======================================================================
```

---

### 2. Live Webcam Face Scan
Capture a real-time face scan using your computer's webcam:
```bash
python -m src --camera
```
- **Real-time feedback**: A live HUD window displays an alignment guide with a real-time face box.
- **Stability gate**: Keeps tracking until the face is stable for 20 frames before capturing.
- **Controls**: Press **[SPACE]** to capture immediately, or **[Q]** to cancel.

---

### 3. Interactive Web Application (FastAPI + React) 🌐
Launch the full-stack web application:
```bash
python -m src --server
```
Open **[http://localhost:8000](http://localhost:8000)** in any browser.
- **Live Webcam HUD**: Center your face in the reticle and click **"Capture Face Scan"**.
- **1-Click Sample Testing**: Click **"Use Sample Portrait"** for instant evaluation.
- **Interactive Stepper**: Visualizes all 4 pipeline stages with live progress badges.
- **Identity & Re-Rank Badges**: Displays resolved person entity, canonical biography, and multi-factor quality points.
- **Audit Receipt Export**: 1-click download of the cryptographic receipt JSON.

---

### 4. On-Chain Authenticity & Integrity Audit
Execute the pipeline with an automated on-chain re-verification audit:
```bash
python -m src samples/sample_faces/sample_person.jpg --test-tamper
```
**Audit Output**:
```text
[On-Chain Authenticity & Integrity Audit]: Verifying post data against live Polygon Amoy contract...
  Authentic URL:      https://en.wikipedia.org/wiki/CarryMinati
  Record Keccak Hash: 0xcc38006066ca2393e793a61de00d291c497aa9e852ef3433fbc246a5d90134f7
  Contract Queried:   0xB066F1C56c530189876c4c538D089997Fb5C4398
  On-Chain Exists:    True
  On-Chain Submitter: 0xA61F18071d1f06Cf1879e78457b3696d631B6537
  Audit Result:       NO FRAUD DETECTED -- 100% Authentic & Immutable on Polygon Amoy!
  Tamper-evident verification successfully completed with ZERO fraud!
```

---

### 5. Standalone Module Execution

Each pipeline component can be tested independently:

#### Test SerpAPI Reverse Search:
```bash
python -m src.web_search.serp_search samples/sample_faces/sample_person.jpg
```

#### Test Blockchain Hashing & Payload Canonicalization:
```bash
python -m src.blockchain.chain
```

#### Test Face Detection & 512-D Embedding:
```bash
python -m src.face_detection.detector samples/sample_faces/sample_person.jpg
```

---

## 🧪 Running Automated Tests

Run the full pytest suite:
```bash
python -m pytest tests/ -v
```

**Test Suite Coverage (22 / 22 Passed)**:
- `tests/test_face_detection.py` (6 tests): MTCNN detection, 30% padding crop, camera HUD, roll angle math, yaw proxy symmetry, quality scoring composite gate.
- `tests/test_web_search.py` (12 tests): Social domain detection, deterministic fingerprinting, metadata extraction, cosine similarity orthogonality, candidate verification, SerpAPI Google Lens candidate mapping, URL classification (ephemeral reels vs canonical profiles), profile URL cleaning, multi-factor re-ranking prioritization.
- `tests/test_blockchain.py` (3 tests): Deterministic Keccak-256 hashing, live on-chain anchoring & re-verification, live cryptographic tamper rejection on Polygon Amoy.
- `tests/test_pipeline.py` (1 test): Full LangGraph DAG end-to-end integration test.

---

## ⛓️ Which Blockchain is Used?

**Polygon Amoy EVM Testnet (Chain ID `80002`)**
- **Smart Contract**: [`contracts/PostVerifier.sol`](contracts/PostVerifier.sol)
- **Deployed Contract Address**: [`0xB066F1C56c530189876c4c538D089997Fb5C4398`](https://amoy.polygonscan.com/address/0xB066F1C56c530189876c4c538D089997Fb5C4398)
- **Explorer**: [https://amoy.polygonscan.com/](https://amoy.polygonscan.com/)
- **Fee Model**: EIP-1559 Type-2 transactions with dynamic fee caps (~0.0026 POL per write).
- **Multi-RPC Resilient**: Automatically fails over across `https://rpc-amoy.polygon.technology`, `https://polygon-amoy-bor-rpc.publicnode.com`, and `https://polygon-amoy.drpc.org`.

---

## 📜 Smart Contract Architecture

The [`PostVerifier.sol`](contracts/PostVerifier.sol) contract is written in Solidity `^0.8.19` and provides two primary entrypoints:

1. `storeRecord(bytes32 dataHash)`: Anchors a 32-byte Keccak-256 metadata hash onto the ledger, binding it with `block.timestamp` and `msg.sender`. Reverts if the record already exists, preventing duplicate overwrite attacks.
2. `verifyRecord(bytes32 dataHash) view returns (bool exists, uint256 timestamp, address submitter)`: Read-only query allowing anyone to verify whether a piece of discovered data was anchored, when it was anchored, and by whom.

---

## ⚠️ Known Limitations & Technical Considerations

1. **Near-Duplicate vs Closed Face-Recognition Index**:
   Google Lens / SerpAPI indexes public web pages and social media posts, not private biometric surveillance databases. It excels at finding images the person has actually posted online or public media appearances.
2. **CDN Hotlink Rate Limits**:
   Certain social platforms (e.g. Instagram CDNs) occasionally rate-limit external image downloads. The candidate verifier handles this gracefully by falling back to page metadata and visual match ranking.
3. **Testnet Gas Management**:
   Live blockchain writes require native testnet POL. The pipeline incorporates automatic zero-gas deduplication and EIP-1559 fee optimization to minimize faucet token consumption.

---

## 🎥 Submission & Video Recording Checklist

- [x] **Walkthrough Demo Video**: [Watch on Google Drive](https://drive.google.com/file/d/1BCKwoHe769dVeVuzDKDuARDbxfiuggeA/view?usp=sharing)
- [x] Full source code in GitHub repo
- [x] Part 1: Face detection, landmark quality scoring & 512-D embedding implemented
- [x] Part 2: Real reverse image search (SerpAPI Google Lens), entity resolution & candidate re-ranking implemented
- [x] Part 3: Privacy-preserving live blockchain anchoring (`contracts/PostVerifier.sol` & `chain.py`) on Polygon Amoy
- [x] Part 4: LangGraph orchestrator (`pipeline/orchestrator.py`) connecting all stages
- [x] Comprehensive architectural specification in [`ARCHITECTURE.md`](ARCHITECTURE.md)
- [x] Automated test suite passing (22/22 tests)
- [x] Screen recording demonstrations supported:
  1. CLI image run: `python -m src samples/sample_faces/sample_person.jpg --test-tamper`
  2. Live webcam scan: `python -m src --camera --test-tamper`
  3. Interactive Web UI: `python -m src --server`
  4. Unit test execution: `python -m pytest tests/ -v`
