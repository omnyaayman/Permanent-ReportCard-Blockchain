// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title ReportCard
 * @notice Stores student grades on-chain as immutable, traceable academic
 *         records. Admin-only write access is enforced with the `onlyOwner`
 *         modifier; every state change emits an event so activity can be
 *         traced through the blockchain.
 */
contract ReportCard {
    address public admin;
    bool public paused;

    mapping(address => uint256) public grades;
    mapping(address => bool) private hasGrade;

    address[] private students;

    mapping(address => string) private userNames;
    mapping(address => bool) private registeredUsers;

    // Emitted when a grade is added for a student for the FIRST time.
    event GradeAdded(address indexed student, uint256 grade);
    // Emitted whenever a grade is set (including first-time additions).
    event GradeUpdated(address indexed student, uint256 grade);
    event UserRegistered(address indexed user, string name);
    event OwnershipTransferred(address indexed oldAdmin, address indexed newAdmin);
    event ContractPaused(address indexed admin);
    event ContractResumed(address indexed admin);

    constructor() {
        admin = msg.sender;
        paused = false;
    }

    modifier onlyOwner() {
        require(msg.sender == admin, "Only admin can perform this action");
        _;
    }

    modifier whenNotPaused() {
        require(!paused, "Contract is paused");
        _;
    }

    function getAdmin() public view returns (address) {
        return admin;
    }

    function transferOwnership(address newAdmin) public onlyOwner {
        require(newAdmin != address(0), "Invalid new admin");

        address oldAdmin = admin;
        admin = newAdmin;

        emit OwnershipTransferred(oldAdmin, newAdmin);
    }

    /**
     * @notice Set (or update) a student grade. Reverts if the contract is
     *         paused or the input is invalid.
     */
    function setGrade(address student, uint256 grade) public onlyOwner whenNotPaused {
        _setGrade(student, grade);
    }

    /**
     * @notice Batch set grades for many students in a single transaction.
     */
    function setMultipleGrades(
        address[] memory studentAddresses,
        uint256[] memory studentGrades
    ) public onlyOwner whenNotPaused {
        require(
            studentAddresses.length == studentGrades.length,
            "Arrays length mismatch"
        );

        for (uint256 i = 0; i < studentAddresses.length; i++) {
            _setGrade(studentAddresses[i], studentGrades[i]);
        }
    }

    /// @dev Shared grade logic: validates input and emits the right events.
    function _setGrade(address student, uint256 grade) internal {
        require(student != address(0), "Invalid student address");
        require(grade <= 100, "Invalid grade: must be between 0 and 100");

        if (!hasGrade[student]) {
            students.push(student);
            hasGrade[student] = true;
            emit GradeAdded(student, grade);
        } else {
            emit GradeUpdated(student, grade);
        }

        grades[student] = grade;
    }

    function getGrade(address student) public view returns (uint256) {
        require(hasGrade[student], "Grade not found");
        return grades[student];
    }

    function getTotalStudents() public view returns (uint256) {
        return students.length;
    }

    function getStudentAt(uint256 index) public view returns (address) {
        require(index < students.length, "Invalid index");
        return students[index];
    }

    function pause() public onlyOwner {
        paused = true;
        emit ContractPaused(msg.sender);
    }

    function resume() public onlyOwner {
        paused = false;
        emit ContractResumed(msg.sender);
    }

    function registerUser(string memory name) public whenNotPaused {
        require(bytes(name).length > 0, "Name is required");
        require(!registeredUsers[msg.sender], "User already registered");

        userNames[msg.sender] = name;
        registeredUsers[msg.sender] = true;

        emit UserRegistered(msg.sender, name);
    }

    function getUserName(address user) public view returns (string memory) {
        require(registeredUsers[user], "User not registered");
        return userNames[user];
    }

    function isUserRegistered(address user) public view returns (bool) {
        return registeredUsers[user];
    }
}
