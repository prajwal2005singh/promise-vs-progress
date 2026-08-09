// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title ProgressRegistry
/// @notice Tamper-proof registry for Promise vs Progress.
///         Stores the hash of citizen-submitted evidence and admin-verified
///         progress updates for a government project, so that once a record
///         is written, nobody -- including the platform's own backend --
///         can quietly edit or delete it after the fact.
/// @dev Only content hashes (keccak256 of a photo, report, or progress
///      snapshot) are stored on-chain, never the raw file. The backend
///      keeps the actual file and a pointer (URL) off-chain and uses this
///      contract purely as a public, append-only proof log.
contract ProgressRegistry {
    /// @notice The three kinds of facts this registry can anchor.
    enum RecordType {
        EVIDENCE,           // raw citizen-uploaded photo/report hash
        VERIFIED_PROGRESS,  // evidence that has been approved / cross-confirmed
        AUDIT_UPDATE        // an admin change to a project's official status
    }

    struct Record {
        uint256 projectId;      // internal project id from the Promise vs Progress DB
        uint256 referenceId;    // id of the evidence/proposal row this hash belongs to
        RecordType recordType;
        bytes32 dataHash;       // keccak256 hash of the evidence content
        address submittedBy;    // wallet of whoever anchored this record
        uint256 timestamp;      // block time the record was written
    }

    address public owner;

    /// @dev Wallets allowed to write records (the backend's server wallet,
    ///      plus any other trusted service the owner adds).
    mapping(address => bool) public writers;

    /// @dev Every record ever written, in insertion order. Arrays are
    ///      append-only in Solidity, so this alone gives us immutability.
    Record[] private records;

    /// @dev Quick lookup: has this exact content hash already been anchored?
    ///      Lets the backend / anyone detect duplicate or reused evidence.
    mapping(bytes32 => bool) public hashExists;

    /// @dev All record indexes that belong to a given project, for fast
    ///      "show me the audit trail for project X" queries.
    mapping(uint256 => uint256[]) private projectRecordIndexes;

    event RecordAdded(
        uint256 indexed recordIndex,
        uint256 indexed projectId,
        uint256 indexed referenceId,
        RecordType recordType,
        bytes32 dataHash,
        address submittedBy,
        uint256 timestamp
    );

    event WriterUpdated(address indexed writer, bool allowed);
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    modifier onlyOwner() {
        require(msg.sender == owner, "ProgressRegistry: caller is not the owner");
        _;
    }

    modifier onlyWriter() {
        require(writers[msg.sender], "ProgressRegistry: caller is not an approved writer");
        _;
    }

    constructor() {
        owner = msg.sender;
        writers[msg.sender] = true;
        emit WriterUpdated(msg.sender, true);
    }

    /// @notice Grant or revoke permission for an address to anchor records.
    ///         In production this is the backend's server wallet; kept
    ///         separate from `owner` so the signing key used day-to-day
    ///         can be rotated without losing contract ownership.
    function setWriter(address writer, bool allowed) external onlyOwner {
        writers[writer] = allowed;
        emit WriterUpdated(writer, allowed);
    }

    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "ProgressRegistry: new owner is the zero address");
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
    }

    /// @notice Anchor a new hash on-chain. Called by the backend whenever a
    ///         citizen uploads evidence, an admin verifies progress, or a
    ///         project's status is officially updated.
    /// @param projectId internal DB id of the project this record concerns
    /// @param referenceId internal DB id of the evidence/proposal row
    /// @param recordType which kind of record this is
    /// @param dataHash keccak256 hash of the underlying content
    /// @return recordIndex the index of the newly created record
    function addRecord(
        uint256 projectId,
        uint256 referenceId,
        RecordType recordType,
        bytes32 dataHash
    ) external onlyWriter returns (uint256 recordIndex) {
        require(dataHash != bytes32(0), "ProgressRegistry: empty hash");

        records.push(
            Record({
                projectId: projectId,
                referenceId: referenceId,
                recordType: recordType,
                dataHash: dataHash,
                submittedBy: msg.sender,
                timestamp: block.timestamp
            })
        );

        recordIndex = records.length - 1;
        hashExists[dataHash] = true;
        projectRecordIndexes[projectId].push(recordIndex);

        emit RecordAdded(
            recordIndex,
            projectId,
            referenceId,
            recordType,
            dataHash,
            msg.sender,
            block.timestamp
        );
    }

    /// @notice Total number of records ever written.
    function recordCount() external view returns (uint256) {
        return records.length;
    }

    /// @notice Fetch a single record by its index.
    function getRecord(uint256 index) external view returns (Record memory) {
        require(index < records.length, "ProgressRegistry: index out of range");
        return records[index];
    }

    /// @notice All record indexes belonging to a project, for building an
    ///         audit trail in the UI.
    function getProjectRecordIndexes(uint256 projectId) external view returns (uint256[] memory) {
        return projectRecordIndexes[projectId];
    }

    /// @notice Cheap existence check -- lets anyone (backend, or a citizen
    ///         verifying a claim independently) confirm a given file hash
    ///         was genuinely anchored on-chain, without reading full records.
    function isHashAnchored(bytes32 dataHash) external view returns (bool) {
        return hashExists[dataHash];
    }
}
