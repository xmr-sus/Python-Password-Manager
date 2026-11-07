# 🔐 Python Password Manager

A console-based password manager built with Python, designed to securely store and manage account credentials using modern cryptographic techniques.

## ✨ Features

- Master password authentication
- Argon2id password hashing and key derivation
- AES-256-GCM authenticated encryption
- Envelope encryption and secure key management
- Add, view, search, update, and delete accounts
- Unique account identification using UUIDs
- Persistent local JSON storage
- Input validation and error handling
- Modular project architecture

## 🛠️ Technologies Used

- Python
- Argon2id (`argon2-cffi`)
- AES-GCM (`cryptography`)
- JSON
- UUID

## 📦 Installation

### 1. Clone the repository

```bash
git clone YOUR_REPOSITORY_URL
```

### 2. Navigate to the project directory

```bash
cd Python-Password-Manager
```

### 3. Create a virtual environment

```bash
python -m venv .venv
```

### 4. Activate the virtual environment

**Windows:**

```bash
.venv\Scripts\activate
```

**Linux / macOS:**

```bash
source .venv/bin/activate
```

### 5. Install dependencies

```bash
pip install argon2-cffi cryptography
```

## 🚀 Usage

Start the application:

```bash
python main.py
```

On the first launch, create a master password. On subsequent launches, authenticate using your master password to access your vault.

The application automatically creates the required JSON storage files when needed.

## 🔒 Security

This project implements multiple layers of security:

- Argon2id for password hashing and key derivation.
- AES-256-GCM for authenticated encryption.
- Randomly generated salts and nonces.
- Envelope encryption to separate the vault key from the master password.
- Encrypted local account storage.

**Disclaimer:** This is an educational project and has not undergone an independent security audit. Keep backups of your vault data. Losing your master password may result in permanent loss of access to your vault.

## 🎯 Learning Objectives

Built to gain practical experience with:

- Python and modular programming
- File handling and JSON persistence
- Authentication and password hashing
- Cryptography and encryption
- Key derivation and key management
- Error handling and software testing

## 👨‍💻 Author

Developed as a personal Python and cybersecurity learning project.
