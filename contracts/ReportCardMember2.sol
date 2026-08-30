// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract GradeCoin {
    string public name = "Grade Coin";
    string public symbol = "GRC";
    uint8 public decimals = 18;

    uint public totalSupply;
    uint public totalMinted;
    address public admin;

    mapping(address => uint) public balanceOf;
    mapping(address => mapping(address => uint)) public allowance;

    event Transfer(address indexed from, address indexed to, uint value);
    event Approval(address indexed owner, address indexed spender, uint value);
    event OwnershipTransferred(address indexed oldAdmin, address indexed newAdmin);

    constructor() {
        admin = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == admin, "Not admin");
        _;
    }

    function getAdmin() public view returns (address) {
        return admin;
    }

    function mint(address to, uint amount) public onlyOwner {
        require(to != address(0), "Invalid address");
        require(amount > 0, "Amount must be greater than zero");

        uint finalAmount = amount * (10 ** decimals);

        balanceOf[to] += finalAmount;
        totalSupply += finalAmount;
        totalMinted += finalAmount;

        emit Transfer(address(0), to, finalAmount);
    }

    function transfer(address to, uint amount) public returns (bool) {
        require(to != address(0), "Invalid address");

        uint finalAmount = amount * (10 ** decimals);

        require(balanceOf[msg.sender] >= finalAmount, "Not enough balance");

        balanceOf[msg.sender] -= finalAmount;
        balanceOf[to] += finalAmount;

        emit Transfer(msg.sender, to, finalAmount);
        return true;
    }

    function approve(address spender, uint amount) public returns (bool) {
        require(spender != address(0), "Invalid spender address");

        uint finalAmount = amount * (10 ** decimals);

        allowance[msg.sender][spender] = finalAmount;

        emit Approval(msg.sender, spender, finalAmount);
        return true;
    }

    function transferFrom(
        address from,
        address to,
        uint amount
    ) public returns (bool) {
        require(from != address(0), "Invalid sender address");
        require(to != address(0), "Invalid receiver address");

        uint finalAmount = amount * (10 ** decimals);

        require(balanceOf[from] >= finalAmount, "Not enough balance");
        require(allowance[from][msg.sender] >= finalAmount, "Allowance exceeded");

        balanceOf[from] -= finalAmount;
        balanceOf[to] += finalAmount;
        allowance[from][msg.sender] -= finalAmount;

        emit Transfer(from, to, finalAmount);
        return true;
    }

    function transferOwnership(address newAdmin) public onlyOwner {
        require(newAdmin != address(0), "Invalid admin address");
        require(newAdmin != admin, "New admin is already admin");

        address oldAdmin = admin;
        admin = newAdmin;

        emit OwnershipTransferred(oldAdmin, newAdmin);
    }
}