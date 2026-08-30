<div align="center">

# <img src="https://readme-typing-svg.herokuapp.com?font=Orbitron&weight=900&size=42&duration=3000&pause=1000&color=58A6FF&background=0D111700&center=true&vCenter=true&width=1000&height=80&lines=Permanent+Report+Card+System;Blockchain+Academic+Platform;Secure+%7C+Transparent+%7C+Tamper-Proof;Built+With+Solidity+%26+Web3.py" />

<img src="https://capsule-render.vercel.app/api?type=waving&height=250&color=0:0D1117,50:161B22,100:1F6FEB&text=WEB3%20REPORT%20CARD&fontAlign=50&fontAlignY=38&fontSize=42&fontColor=ffffff&animation=fadeIn"/>


<img src="https://img.shields.io/badge/Solidity-Smart%20Contracts-1F6FEB?style=for-the-badge&logo=solidity&logoColor=white"/>
<img src="https://img.shields.io/badge/Web3.py-Blockchain%20Interaction-111827?style=for-the-badge"/>
<img src="https://img.shields.io/badge/Ethereum-Decentralized%20Network-627EEA?style=for-the-badge&logo=ethereum&logoColor=white"/>
<img src="https://img.shields.io/badge/Python-Automation%20Scripts-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
<img src="https://img.shields.io/badge/Status-Completed-success?style=for-the-badge"/>

</div>

---

# 📌 About The Project

Permanent Report Card System is a blockchain-based academic platform that stores student grades securely on Ethereum smart contracts.

The system guarantees that grades become:

* ✅ Permanent
* ✅ Secure
* ✅ Transparent
* ✅ Tamper-Proof

This project combines Solidity smart contracts with Python Web3 applications to create a fully decentralized academic management system.

---

# 🚀 Main Features

## 👑 Admin Features

* Add student grades (`GradeAdded` event)
* Update existing grades (`GradeUpdated` event)
* Batch grade operations with `setMultipleGrades`
* Total student / student-at-index lookups
* Mint Grade Coins
* Pause & resume the system
* Transfer ownership to another admin
* Blockchain analytics dashboard
* Automatic deployment & setup

---

## 👨‍🎓 User Features

* Register wallet profile
* Save display name
* View grades
* Check Grade Coin balance
* Check ETH balance
* View blockchain activity history
* Blockchain interaction through CLI & GUI apps

---

# 🔐 Smart Contract Security

```diff id="0sgjvk"
+ onlyOwner modifier
+ whenNotPaused modifier
+ Ownership transfer protection
+ Unauthorized access testing
+ Blockchain event monitoring
```

---

# 🪙 Grade Coin System

The platform includes a custom blockchain token called:

## Grade Coin

### Features:

* Mintable only by Admin
* Balance tracking
* Reward distribution
* ETH + Token balance checking
* CSV snapshot exporting

---

# 📡 Live Alert System

Whenever a grade changes on-chain:

```bash id="88b5o7"
ALERT: A grade change just happened!
```

---

# 📊 Blockchain Analytics

The Admin Dashboard scans blockchain history and generates:

* Total grades stored
* Total Grade Coins minted
* Total transactions
* Most active wallet addresses
* Class average reports
* Account balance snapshots

---

# 🖥 Applications

## 💻 CLI Application

```bash id="jlwmj0"
python scripts/cli_app.py
```

---

## 🪟 GUI Application (Streamlit)

```bash id="l5fx1n"
streamlit run scripts/gui_app.py
```

Pages: Admin Dashboard, Student Portal, Admin Actions, System Info.

---

# ⚙ Installation

## 📥 Clone Repository

```bash id="wz3efh"
git clone YOUR_REPOSITORY_LINK
cd Permanent-ReportCard-Blockchain
```

---

## 📦 Install Requirements

```bash id="w8m08o"
pip install -r requirements.txt
```

## 🔑 Configure Environment

Copy the template and fill in your local values:

```bash
cp .env.example .env
```

`.env` holds `RPC_URL`, `ADMIN_ADDRESS`, `ADMIN_PASSWORD` (demo-only CLI/GUI
password gate; the smart contract enforces real admin authority on-chain) and
an optional `EXPLORER_URL`. **Never commit your real `.env`.**

---

## ⛓ Start Ganache

```bash id="gv2wt6"
npx ganache --port 7545
# or Ganache GUI: http://127.0.0.1:7545
```

---

## 🚀 Deploy Smart Contracts

```bash id="mqvjlwm"
python scripts/deploy_and_setup.py
```

---

# 📂 Project Structure

```bash id="0eg4p6"
Permanent-ReportCard-Blockchain/
│
├── contracts/
│   ├── ReportCard.sol
│   └── ReportCardMember2.sol   (deploys the "GradeCoin" token contract)
│
├── scripts/
│   ├── admin_dashboard.py
│   ├── blockchain_scanner.py
│   ├── cli_app.py
│   ├── config.py
│   ├── deploy_and_setup.py
│   ├── gui_app.py
│   ├── history_report.py
│   ├── live_alert.py
│   ├── ownership_transfer_test.py
│   ├── security_test.py
│   ├── snapshot_exporter.py
│   ├── styles.py
│   └── utils.py
│
├── tests/
│   └── test_contracts.py, test_utils.py
│
├── outputs/            (runtime data, gitignored)
│
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
└── run_all.bat
```

---

# 🧪 Testing

Unit + integration tests (contract ABI, utils, admin/ownership rules):

```bash id="7d0i9u"
python -m unittest discover -s tests
```

**31 tests passing** (24 contract tests + 7 utils tests).

Security tests (prove unauthorized users cannot perform admin-only actions):

```bash
python scripts/security_test.py   # Expect 7/7 passed
python scripts/ownership_transfer_test.py
```

Other scripts, against a running Ganache:

```bash
python scripts/deploy_and_setup.py
python scripts/blockchain_scanner.py
python scripts/history_report.py
python scripts/live_alert.py
python scripts/snapshot_exporter.py
python scripts/admin_dashboard.py
```

---

# 🛠 Technologies Used

<div align="center">

| Technology | Usage                  |
| ---------- | ---------------------- |
| Solidity   | Smart Contracts        |
| Python     | Backend Scripts        |
| Web3.py    | Blockchain Interaction |
| Streamlit  | Web GUI                |
| Ethereum   | Decentralized Network  |
| Ganache    | Local Blockchain       |
| CSV / JSON | Data Export            |

</div>

---

# 🎯 Educational Purpose

This project was developed as a university blockchain project focused on:

* Smart Contract Security
* Blockchain Analytics
* Ethereum Development
* Web3 Integration
* Decentralized Academic Systems

---
