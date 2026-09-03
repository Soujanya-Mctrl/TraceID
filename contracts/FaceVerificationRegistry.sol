// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title FaceVerificationRegistry
 * @dev Immutable on-chain registry for anchoring face-to-social-media discovery proofs.
 * Provides verifiable, tamper-evident proof that a specific face scan was matched
 * with authentic public social media content at a verified point in time.
 */
contract FaceVerificationRegistry {
    
    struct VerificationRecord {
        bytes32 recordHash;        // Keccak-256 composite hash (face + post + metadata)
        bytes32 faceHash;          // Biometric hash of the face encoding vector
        bytes32 postContentHash;   // Hash of the discovered post content (text/media)
        string postUrl;            // Canonical social media post URL
        string platform;           // Social platform name (e.g., "X", "LinkedIn")
        uint256 timestamp;         // Blockchain timestamp when anchored
        address submitter;         // Wallet address that anchored the record
        bool exists;               // Existence flag
    }

    // Mapping from recordHash to VerificationRecord
    mapping(bytes32 => VerificationRecord) private _records;
    
    // Ordered list of all anchored record hashes
    bytes32[] private _recordHashes;

    // Events for transparent indexer & observer tracking
    event RecordAnchored(
        bytes32 indexed recordHash,
        bytes32 indexed faceHash,
        string postUrl,
        address indexed submitter,
        uint256 timestamp
    );

    event VerificationQueried(
        bytes32 indexed recordHash,
        bool exists,
        address indexed verifier
    );

    error RecordAlreadyExists(bytes32 recordHash);
    error RecordNotFound(bytes32 recordHash);
    error EmptyParameter();

    /**
     * @notice Anchors a new face-to-post discovery record onto the blockchain.
     * @param recordHash The composite keccak256 hash of (faceHash, postContentHash, postUrl, timestamp)
     * @param faceHash The SHA-256 / Keccak-256 fingerprint of the normalized face encoding
     * @param postContentHash The cryptographic hash of the discovered post's content and media
     * @param postUrl The public URL of the discovered social media post
     * @param platform The name of the social media platform
     */
    function anchorRecord(
        bytes32 recordHash,
        bytes32 faceHash,
        bytes32 postContentHash,
        string calldata postUrl,
        string calldata platform
    ) external returns (bool) {
        if (recordHash == bytes32(0) || faceHash == bytes32(0)) {
            revert EmptyParameter();
        }
        if (_records[recordHash].exists) {
            revert RecordAlreadyExists(recordHash);
        }

        _records[recordHash] = VerificationRecord({
            recordHash: recordHash,
            faceHash: faceHash,
            postContentHash: postContentHash,
            postUrl: postUrl,
            platform: platform,
            timestamp: block.timestamp,
            submitter: msg.sender,
            exists: true
        });

        _recordHashes.push(recordHash);

        emit RecordAnchored(recordHash, faceHash, postUrl, msg.sender, block.timestamp);
        return true;
    }

    /**
     * @notice Verifies whether a given record exists on-chain and retrieves its immutable proof data.
     * @param recordHash The composite hash to query
     * @return exists Whether the record has been anchored
     * @return faceHash The biometric face hash anchored
     * @return postContentHash The post content hash anchored
     * @return postUrl The social media URL
     * @return platform The platform name
     * @return timestamp The block timestamp when anchored
     * @return submitter The submitter's wallet address
     */
    function verifyRecord(bytes32 recordHash) external view returns (
        bool exists,
        bytes32 faceHash,
        bytes32 postContentHash,
        string memory postUrl,
        string memory platform,
        uint256 timestamp,
        address submitter
    ) {
        VerificationRecord memory rec = _records[recordHash];
        return (
            rec.exists,
            rec.faceHash,
            rec.postContentHash,
            rec.postUrl,
            rec.platform,
            rec.timestamp,
            rec.submitter
        );
    }

    /**
     * @notice Checks if a record exists on chain.
     */
    function isRecordValid(bytes32 recordHash) external view returns (bool) {
        return _records[recordHash].exists;
    }

    /**
     * @notice Returns total count of anchored records.
     */
    function getRecordCount() external view returns (uint256) {
        return _recordHashes.length;
    }

    /**
     * @notice Retrieves record hash by its sequential index.
     */
    function getRecordHashByIndex(uint256 index) external view returns (bytes32) {
        require(index < _recordHashes.length, "Index out of bounds");
        return _recordHashes[index];
    }
}
