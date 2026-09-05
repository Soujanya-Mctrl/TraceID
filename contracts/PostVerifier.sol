// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title PostVerifier
 * @dev Privacy-preserving blockchain anchoring for discovered web & social posts.
 *
 * PRIVACY DESIGN PRINCIPLE:
 * Only non-biometric metadata about the matched post is hashed into a 32-byte
 * Keccak-256 fingerprint and anchored on-chain.
 * NEVER stores face embeddings, raw biometric vectors, or image bytes on-chain.
 */
contract PostVerifier {
    struct Record {
        uint256 timestamp;
        address submitter;
        bool exists;
    }

    // Mapping from 32-byte payload hash to Record
    mapping(bytes32 => Record) private records;

    // Events for transparent on-chain auditability
    event RecordStored(bytes32 indexed dataHash, address indexed submitter, uint256 timestamp);

    /**
     * @notice Anchors a 32-byte metadata hash onto the blockchain.
     * @dev Reverts if the exact same hash was already stored (prevents silent duplicates).
     * @param dataHash 32-byte keccak256 hash of canonical post metadata.
     */
    function storeRecord(bytes32 dataHash) external {
        require(dataHash != bytes32(0), "Invalid data hash");
        require(!records[dataHash].exists, "Record already exists");

        records[dataHash] = Record({
            timestamp: block.timestamp,
            submitter: msg.sender,
            exists: true
        });

        emit RecordStored(dataHash, msg.sender, block.timestamp);
    }

    /**
     * @notice Re-verifies a 32-byte metadata hash against the on-chain ledger.
     * @param dataHash 32-byte keccak256 hash to query.
     * @return exists True if the record was previously anchored, False otherwise.
     * @return timestamp Block timestamp when the record was anchored (0 if not exists).
     * @return submitter Ethereum address that submitted the transaction (address(0) if not exists).
     */
    function verifyRecord(bytes32 dataHash)
        external
        view
        returns (
            bool exists,
            uint256 timestamp,
            address submitter
        )
    {
        Record memory r = records[dataHash];
        return (r.exists, r.timestamp, r.submitter);
    }
}
