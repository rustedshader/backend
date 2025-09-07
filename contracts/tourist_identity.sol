// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/token/ERC721/ERC721.sol";

/**
 * @title TouristID
 * @dev Non-transferable (SBT-style) ERC721 for tourist digital IDs.
 * Only the owner (backend) can issue/revoke. Stores hashes for privacy.
 */
contract TouristID is ERC721, Ownable {
    using Counters for Counters.Counter;
    Counters.Counter private _tokenIdCounter;

    struct TouristInfo {
        bytes32 kycHash;        // e.g., SHA-256 or keccak256 off-chain hash
        bytes32 itineraryHash;  // e.g., trip details hash
        uint256 validUntil;     // unix timestamp
        bool isRevoked;
    }

    mapping(uint256 => TouristInfo) private _touristData;

    event IDIssued(
        uint256 indexed tokenId,
        address indexed tourist,
        bytes32 kycHash,
        uint256 validUntil
    );
    event IDRevoked(uint256 indexed tokenId);

    constructor() ERC721("Tourist Digital ID", "TID") Ownable(msg.sender) {}

    /**
     * @notice Issue a new ID. Only owner.
     */
    function issueID(
        address tourist,
        bytes32 kycHash,
        bytes32 itineraryHash,
        uint256 validityDuration
    ) public onlyOwner returns (uint256) {
        require(tourist != address(0), "Tourist address cannot be zero");
        require(validityDuration > 0, "Validity must be > 0");

        _tokenIdCounter.increment();
        uint256 newTokenId = _tokenIdCounter.current();

        uint256 expirationTimestamp = block.timestamp + validityDuration;

        _safeMint(tourist, newTokenId);

        _touristData[newTokenId] = TouristInfo({
            kycHash: kycHash,
            itineraryHash: itineraryHash,
            validUntil: expirationTimestamp,
            isRevoked: false
        });

        emit IDIssued(newTokenId, tourist, kycHash, expirationTimestamp);
        return newTokenId;
    }

    /**
     * @notice Revoke an ID. Only owner.
     */
    function revokeID(uint256 tokenId) public onlyOwner {
        require(_ownerOf(tokenId) != address(0), "ID does not exist");
        _touristData[tokenId].isRevoked = true;
        emit IDRevoked(tokenId);
    }

    /**
     * @notice Check if an ID is valid (exists, not revoked, not expired).
     */
    function isValid(uint256 tokenId) public view returns (bool) {
        if (_ownerOf(tokenId) == address(0)) return false;
        TouristInfo storage info = _touristData[tokenId];
        return !info.isRevoked && block.timestamp < info.validUntil;
    }

    /**
     * @notice Get stored info for a tokenId.
     */
    function getTouristInfo(uint256 tokenId)
        public
        view
        returns (TouristInfo memory)
    {
        require(_ownerOf(tokenId) != address(0), "ID does not exist");
        return _touristData[tokenId];
    }

    // --- Soul-Bound (non-transferable) logic for OZ v5 ---
    // In OZ v5, override _update (centralized state change for mint/transfer/burn).
    // Allow only mint (from == 0) and burn (to == 0). Block wallet-to-wallet transfers.
    function _update(address to, uint256 tokenId, address auth)
        internal
        virtual
        override
        returns (address from)
    {
        address currentOwner = _ownerOf(tokenId); // pre-state
        bool isMint = currentOwner == address(0);
        bool isBurn = to == address(0);

        // Disallow transfers where both from and to are non-zero (i.e., regular transfers)
        if (!isMint && !isBurn) {
            revert("This token is non-transferable");
        }

        // Proceed with mint or burn
        from = super._update(to, tokenId, auth);
    }
}
