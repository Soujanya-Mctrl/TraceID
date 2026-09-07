import React, { useState, useRef, useEffect } from 'react';
import {
  ShieldCheck,
  Camera,
  UploadCloud,
  Search,
  Link,
  ExternalLink,
  AlertTriangle,
  FileCheck,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Cpu,
  Database,
  Lock,
  Download,
  Eye,
  Sliders
} from 'lucide-react';
import confetti from 'canvas-confetti';

export default function App() {
  const [activeTab, setActiveTab] = useState('upload'); // 'upload' | 'camera'
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [statusInfo, setStatusInfo] = useState(null);

  // Camera state
  const [isCameraActive, setIsCameraActive] = useState(false);
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  // Processing state
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState(0); // 0=idle, 1=detect, 2=search, 3=blockchain, 4=done
  const [stepMessage, setStepMessage] = useState('');
  const [verificationResult, setVerificationResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  // Tamper test state
  const [isTampering, setIsTampering] = useState(false);
  const [tamperResult, setTamperResult] = useState(null);

  // Load system status on mount
  useEffect(() => {
    fetch('/api/status')
      .then(res => res.json())
      .then(data => setStatusInfo(data))
      .catch(err => console.error('Status fetch failed:', err));
  }, []);

  // Cleanup camera stream
  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setIsCameraActive(false);
  };

  const startCamera = async () => {
    try {
      setErrorMessage(null);
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: 'user' },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setIsCameraActive(true);
    } catch (err) {
      setErrorMessage('Could not access webcam: ' + err.message);
      setIsCameraActive(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'camera') {
      startCamera();
    } else {
      stopCamera();
    }
    return () => stopCamera();
  }, [activeTab]);

  const handleCaptureSnapshot = () => {
    if (!videoRef.current) return;
    const canvas = document.createElement('canvas');
    canvas.width = videoRef.current.videoWidth || 640;
    canvas.height = videoRef.current.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    // Mirror the snapshot to match video view
    ctx.translate(canvas.width, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
    const dataUrl = canvas.toDataURL('image/jpeg', 0.95);
    setPreviewUrl(dataUrl);
    setSelectedFile(null); // using base64
    stopCamera();
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setVerificationResult(null);
    setTamperResult(null);
    setErrorMessage(null);
  };

  const handleLoadSample = async () => {
    try {
      setErrorMessage(null);
      const res = await fetch('/output/sample_person.jpg').catch(() => null);
      // Fallback load from static
      setPreviewUrl('/output/face_crop.jpg');
      setSelectedFile(null);
    } catch (e) {
      setErrorMessage('Could not load sample face.');
    }
  };

  const runVerification = async () => {
    setIsProcessing(true);
    setVerificationResult(null);
    setTamperResult(null);
    setErrorMessage(null);
    setCurrentStep(1);
    setStepMessage('Detecting face & evaluating landmark quality...');

    try {
      const formData = new FormData();
      if (selectedFile) {
        formData.append('file', selectedFile);
      } else if (previewUrl && previewUrl.startsWith('data:')) {
        formData.append('image_base64', previewUrl);
      } else {
        // Sample person fallback
        const blobRes = await fetch('/output/face_crop.jpg');
        const blob = await blobRes.blob();
        formData.append('file', blob, 'sample_face.jpg');
      }

      // Step progress timer for smooth UX while backend processes
      const stepTimer1 = setTimeout(() => {
        setCurrentStep(2);
        setStepMessage('Searching web via SerpAPI Google Lens & verifying faces...');
      }, 3500);

      const stepTimer2 = setTimeout(() => {
        setCurrentStep(3);
        setStepMessage('Canonicalizing metadata & anchoring Keccak-256 hash to blockchain...');
      }, 7000);

      const response = await fetch('/api/verify', {
        method: 'POST',
        body: formData,
      });

      clearTimeout(stepTimer1);
      clearTimeout(stepTimer2);

      const data = await response.json();
      if (!response.ok || !data.success) {
        throw new Error(data.detail || data.error || 'Verification failed');
      }

      setCurrentStep(4);
      setStepMessage('Completed successfully!');
      setVerificationResult(data);

      if (data.search?.verified) {
        confetti({
          particleCount: 80,
          spread: 70,
          origin: { y: 0.6 },
          colors: ['#38bdf8', '#10b981', '#6366f1'],
        });
      }
    } catch (err) {
      setErrorMessage(err.message || 'An error occurred during pipeline execution.');
      setCurrentStep(0);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleTamperTest = async () => {
    if (!verificationResult) return;
    setIsTampering(true);
    try {
      const res = await fetch('/api/tamper-test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          page_url: verificationResult.search?.matched_page_url,
          original_data_hash: verificationResult.blockchain?.tx_hash || '0x0',
          altered_url: `${verificationResult.search?.matched_page_url}?tamper_auth_bypass=1`,
        }),
      });
      const data = await res.json();
      setTamperResult(data);
    } catch (err) {
      setErrorMessage('Tamper test error: ' + err.message);
    } finally {
      setIsTampering(false);
    }
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-top">
          <div className="logo-group">
            <div className="logo-badge">
              <ShieldCheck size={26} color="#fff" />
            </div>
            <div>
              <h1 className="app-title">TraceID</h1>
              <p className="app-subtitle">
                Privacy-preserving facial biometrics, web entity resolution & immutable blockchain verification
              </p>
            </div>
          </div>
          <div className="system-badges">
            <div className="badge">
              <div className="badge-dot"></div>
              <span>Engine: MTCNN + Facenet512</span>
            </div>
            <div className="badge badge-cyan">
              <Search size={13} />
              <span>Search: {statusInfo?.search_backend?.toUpperCase() || 'SERPAPI'}</span>
            </div>
            <div className="badge badge-purple">
              <Database size={13} />
              <span>Chain: {statusInfo?.blockchain_network || 'Verifiable Ledger'}</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Action Grid */}
      <div className="dashboard-grid">
        {/* Left Column: Input Panel */}
        <div className="card">
          <div className="card-title-group">
            <h2 className="card-title">
              <Camera size={20} color="#38bdf8" />
              Face Input Scan
            </h2>
            <button
              type="button"
              className="btn btn-secondary"
              style={{ padding: '6px 14px', fontSize: '0.8rem' }}
              onClick={handleLoadSample}
            >
              Load Sample Face
            </button>
          </div>

          <div className="tabs-nav">
            <button
              className={`tab-btn ${activeTab === 'upload' ? 'active' : ''}`}
              onClick={() => setActiveTab('upload')}
            >
              <UploadCloud size={16} />
              File Upload
            </button>
            <button
              className={`tab-btn ${activeTab === 'camera' ? 'active' : ''}`}
              onClick={() => setActiveTab('camera')}
            >
              <Camera size={16} />
              Live Webcam HUD
            </button>
          </div>

          {activeTab === 'upload' ? (
            <label className="dropzone">
              <input
                type="file"
                accept="image/jpeg,image/png,image/webp"
                style={{ display: 'none' }}
                onChange={handleFileChange}
              />
              {previewUrl ? (
                <div style={{ textAlign: 'center' }}>
                  <img
                    src={previewUrl}
                    alt="Scan Preview"
                    style={{ maxHeight: '200px', borderRadius: '12px', marginBottom: '12px' }}
                  />
                  <p style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Click to select a different photo</p>
                </div>
              ) : (
                <>
                  <div className="dropzone-icon">
                    <UploadCloud size={28} />
                  </div>
                  <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Drop a portrait photo here</h3>
                  <p style={{ fontSize: '0.85rem', color: '#64748b' }}>Supports JPG, PNG, WebP</p>
                </>
              )}
            </label>
          ) : (
            <div>
              {isCameraActive ? (
                <div className="webcam-box">
                  <video ref={videoRef} autoPlay playsInline muted className="webcam-video" />
                  <div className="hud-reticle">
                    <div className="scan-laser"></div>
                  </div>
                </div>
              ) : (
                <div className="dropzone" onClick={startCamera}>
                  <Camera size={32} color="#38bdf8" />
                  <p>Click to activate live webcam</p>
                </div>
              )}

              {isCameraActive && (
                <div style={{ marginTop: '16px', display: 'flex', gap: '12px' }}>
                  <button className="btn btn-primary" style={{ flex: 1 }} onClick={handleCaptureSnapshot}>
                    <Camera size={18} />
                    Capture Face Scan
                  </button>
                  <button className="btn btn-secondary" onClick={stopCamera}>
                    Cancel
                  </button>
                </div>
              )}
            </div>
          )}

          {previewUrl && !isCameraActive && (
            <div style={{ marginTop: '20px' }}>
              <button
                className="btn btn-primary"
                style={{ width: '100%' }}
                disabled={isProcessing}
                onClick={runVerification}
              >
                {isProcessing ? (
                  <>
                    <div className="spinner"></div>
                    Executing Pipeline...
                  </>
                ) : (
                  <>
                    <ShieldCheck size={18} />
                    Run Identification & Verification
                  </>
                )}
              </button>
            </div>
          )}

          {errorMessage && (
            <div style={{ marginTop: '16px', padding: '12px', background: 'rgba(244, 63, 94, 0.15)', borderRadius: '8px', color: '#f43f5e', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <AlertTriangle size={16} />
              {errorMessage}
            </div>
          )}
        </div>

        {/* Right Column: Execution Status & Privacy Note */}
        <div className="card">
          <h2 className="card-title" style={{ marginBottom: '16px' }}>
            <Lock size={20} color="#10b981" />
            Zero-Biometric Privacy Rule
          </h2>
          <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginBottom: '20px', lineHeight: 1.6 }}>
            Public blockchains are permanent and public. To preserve identity privacy, this system strictly enforces the <strong>Metadata-Only Anchoring Principle</strong>:
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '24px' }}>
            <div style={{ padding: '14px', background: 'rgba(244, 63, 94, 0.08)', borderRadius: '10px', border: '1px solid rgba(244, 63, 94, 0.2)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#f43f5e', fontWeight: 600, fontSize: '0.85rem', marginBottom: '6px' }}>
                <XCircle size={15} />
                NEVER On-Chain
              </div>
              <ul style={{ fontSize: '0.8rem', color: '#94a3b8', listStylePosition: 'inside' }}>
                <li>Raw Face Pixels</li>
                <li>Biometric Embeddings</li>
                <li>Personal Identifiers</li>
              </ul>
            </div>

            <div style={{ padding: '14px', background: 'rgba(16, 185, 129, 0.08)', borderRadius: '10px', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#10b981', fontWeight: 600, fontSize: '0.85rem', marginBottom: '6px' }}>
                <CheckCircle2 size={15} />
                Anchored On-Chain
              </div>
              <ul style={{ fontSize: '0.8rem', color: '#94a3b8', listStylePosition: 'inside' }}>
                <li>Canonical Keccak-256</li>
                <li>Discovered Post URL</li>
                <li>Block Timestamp</li>
              </ul>
            </div>
          </div>

          <div style={{ padding: '16px', background: 'rgba(0,0,0,0.2)', borderRadius: '10px', fontSize: '0.85rem', color: '#64748b' }}>
            <div style={{ fontWeight: 600, color: '#94a3b8', marginBottom: '4px' }}>Smart Contract:</div>
            <code style={{ color: '#38bdf8', wordBreak: 'break-all' }}>
              {statusInfo?.contract_address || 'PostVerifier.sol (Polygon Amoy)'}
            </code>
          </div>
        </div>
      </div>

      {/* Pipeline Progress Stepper */}
      {(isProcessing || currentStep > 0) && (
        <div className="card stepper-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Cpu size={18} color="#38bdf8" />
              Pipeline Execution Flow
            </h3>
            <span style={{ fontSize: '0.85rem', color: '#38bdf8', fontWeight: 500 }}>{stepMessage}</span>
          </div>

          <div className="stepper">
            <div className="stepper-progress-bar">
              <div
                className="stepper-progress-fill"
                style={{
                  width:
                    currentStep === 1 ? '25%' :
                    currentStep === 2 ? '50%' :
                    currentStep === 3 ? '75%' :
                    currentStep === 4 ? '100%' : '0%',
                }}
              ></div>
            </div>

            <div className={`step-item ${currentStep >= 1 ? 'active' : ''} ${currentStep > 1 ? 'completed' : ''}`}>
              <div className="step-circle">1</div>
              <div className="step-label">Face Quality</div>
              <div className="step-desc">MTCNN & Blur/Tilt Gate</div>
            </div>

            <div className={`step-item ${currentStep >= 2 ? 'active' : ''} ${currentStep > 2 ? 'completed' : ''}`}>
              <div className="step-circle">2</div>
              <div className="step-label">Web Search</div>
              <div className="step-desc">SerpAPI Google Lens</div>
            </div>

            <div className={`step-item ${currentStep >= 3 ? 'active' : ''} ${currentStep > 3 ? 'completed' : ''}`}>
              <div className="step-circle">3</div>
              <div className="step-label">Face & Identity Matching</div>
              <div className="step-desc">Cosine Similarity &ge; 0.70 &amp; Canonical Resolution</div>
            </div>

            <div className={`step-item ${currentStep >= 4 ? 'completed' : ''}`}>
              <div className="step-circle">4</div>
              <div className="step-label">Blockchain</div>
              <div className="step-desc">PostVerifier Anchoring</div>
            </div>
          </div>
        </div>
      )}

      {/* Verification Results Card */}
      {verificationResult && (
        <div className="card result-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <CheckCircle2 size={28} color="#10b981" />
              <div>
                <h3 style={{ fontSize: '1.3rem', fontWeight: 700 }}>Verification Complete</h3>
                <p style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
                  Execution time: {verificationResult.elapsed_sec}s
                </p>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <a
                href="/api/receipt"
                download="verification_receipt.json"
                className="btn btn-secondary"
                style={{ padding: '8px 16px', fontSize: '0.85rem' }}
              >
                <Download size={14} />
                Download Receipt JSON
              </a>
            </div>
          </div>

          {/* Visual Comparison Grid */}
          <div className="comparison-grid">
            <div className="comparison-image-box">
              <img
                src={verificationResult.face?.crop_base64 || verificationResult.face?.crop_image_url}
                alt="Original Face Crop"
                className="comparison-img"
              />
              <span style={{ fontSize: '0.85rem', color: '#94a3b8', fontWeight: 600 }}>Input Face Crop</span>
            </div>

            <div className="comparison-vs">
              <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#64748b' }}>
                Cosine Similarity
              </span>
              <div className="similarity-badge">
                {verificationResult.search?.similarity
                  ? (verificationResult.search.similarity * 100).toFixed(1) + '%'
                  : 'VERIFIED'}
              </div>
              <span style={{ fontSize: '0.75rem', color: '#10b981', fontWeight: 600 }}>
                {verificationResult.search?.verified ? '&ge; 0.70 Threshold Pass' : (verificationResult.search?.identified_entity ? 'Canonical Match' : 'Ranked Match')}
              </span>
            </div>

            <div className="comparison-image-box">
              {verificationResult.search?.matched_image_url ? (
                <img
                  src={verificationResult.search.matched_image_url}
                  alt="Discovered Candidate"
                  className="comparison-img"
                />
              ) : (
                <div className="comparison-img" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#1e293b', color: '#64748b', fontSize: '0.75rem', textAlign: 'center', padding: '10px' }}>
                  Web Context Image
                </div>
              )}
              <span style={{ fontSize: '0.85rem', color: '#94a3b8', fontWeight: 600 }}>Discovered Web Image</span>
            </div>
          </div>

          {/* Data Table */}
          <table className="data-table">
            <tbody>
              {verificationResult.search?.identified_entity && (
                <tr>
                  <td>Identified Identity</td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                      <span style={{ fontWeight: 700, color: '#f8fafc', fontSize: '1rem' }}>
                        {verificationResult.search.identified_entity}
                      </span>
                      {verificationResult.search.entity_description && (
                        <span style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
                          ({verificationResult.search.entity_description})
                        </span>
                      )}
                      <span className="badge badge-purple" style={{ fontSize: '0.7rem' }}>
                        Canonical Resolution
                      </span>
                    </div>
                  </td>
                </tr>
              )}
              <tr>
                <td>Canonical Profile / Post URL</td>
                <td>
                  <a
                    href={verificationResult.search?.matched_page_url}
                    target="_blank"
                    rel="noreferrer"
                    style={{ color: '#38bdf8', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '6px' }}
                  >
                    {verificationResult.search?.matched_page_url}
                    <ExternalLink size={14} />
                  </a>
                </td>
              </tr>
              <tr>
                <td>Platform / Category</td>
                <td>
                  <span className="badge badge-cyan">{verificationResult.search?.platform}</span>
                </td>
              </tr>
              {verificationResult.search?.rerank_score !== undefined && (
                <tr>
                  <td>Re-Rank Quality Score</td>
                  <td>
                    <span style={{ color: '#38bdf8', fontWeight: 600 }}>
                      {verificationResult.search.rerank_score} pts
                    </span>
                    <span style={{ fontSize: '0.75rem', color: '#64748b', marginLeft: '8px' }}>
                      (Multi-factor: Biometric + Authority + Anti-Reel)
                    </span>
                  </td>
                </tr>
              )}
              <tr>
                <td>Blockchain Transaction</td>
                <td style={{ color: '#c084fc' }}>{verificationResult.blockchain?.tx_hash}</td>
              </tr>
              <tr>
                <td>On-Chain Verified</td>
                <td>
                  <span style={{ color: '#10b981', fontWeight: 700 }}>
                    {verificationResult.blockchain?.on_chain_exists ? 'TRUE (Verified on Ledger)' : 'FALSE'}
                  </span>
                </td>
              </tr>
              <tr>
                <td>Audit Timestamp</td>
                <td>{new Date(verificationResult.blockchain?.on_chain_timestamp * 1000).toLocaleString()}</td>
              </tr>
            </tbody>
          </table>

          {/* Tamper Demonstration Sandbox */}
          <div className="tamper-box">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', marginBottom: '14px' }}>
              <div>
                <h4 style={{ fontSize: '1rem', fontWeight: 700, color: '#f43f5e', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <AlertTriangle size={18} />
                  Live Smart Contract Tamper Audit
                </h4>
                <p style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                  Modifies the discovered post URL to prove the live Polygon smart contract catches and rejects fraud.
                </p>
              </div>

              <button
                className="btn btn-danger"
                style={{ padding: '8px 18px', fontSize: '0.85rem' }}
                disabled={isTampering}
                onClick={handleTamperTest}
              >
                {isTampering ? 'Querying Polygon Amoy...' : 'Audit Altered URL Rejection'}
              </button>
            </div>

            {tamperResult && (
              <div style={{ padding: '16px', background: 'rgba(0, 0, 0, 0.4)', borderRadius: '8px', fontSize: '0.85rem' }}>
                <div style={{ color: '#f43f5e', fontWeight: 700, marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <XCircle size={16} />
                  {tamperResult.status}: FORGED DATA DETECTED
                </div>
                <p style={{ color: '#94a3b8', lineHeight: 1.5, marginBottom: '8px' }}>
                  {tamperResult.explanation}
                </p>
                <div style={{ fontFamily: 'monospace', fontSize: '0.75rem', color: '#64748b' }}>
                  <div>Original Hash: {tamperResult.original_hash}</div>
                  <div>Altered Hash:  {tamperResult.altered_hash || tamperResult.forged_hash}</div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
