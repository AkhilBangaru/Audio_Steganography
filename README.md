<img width="2048" height="2048" alt="Logo" src="https://github.com/user-attachments/assets/ef1760bd-c64c-40d2-bfb5-27c6e136dcc3" />

## 🔐 Audio Steganography Web Tool

A secure, password-protected **audio steganography web application** that allows you to hide **text or files inside WAV audio** using **LSB steganography + encryption**.

Built with **Flask** and a custom **StegEngine**, this project focuses on **correctness, security, and clarity** rather than gimmicks.

---

## 🎯 What This Project Does

This tool allows you to:

* 🎵 Hide **text or files** inside `.wav` audio files
* 🔑 Protect hidden data using **password-based encryption**
* 📦 Compress + encrypt payloads before embedding
* 🔍 Safely extract hidden content using the correct password
* 🌐 Use everything via a **simple web interface**

No external steganography tools required.

---

## 🧠 How It Works (High Level)

1. **Payload Preparation**

   * Text or file is converted to bytes
   * Payload format:

     ```
     TYPE|||FILENAME|||DATA
     ```

2. **Security Layer**

   * Payload is compressed using `zlib`
   * Encrypted using **Fernet (AES)**
   * Key derived from password using **PBKDF2-HMAC-SHA256**

3. **Steganography**

   * Encrypted data length is stored first (4 bytes)
   * Payload bits are embedded into **LSB of WAV audio samples**

4. **Extraction**

   * Length is read from LSBs
   * Payload is reconstructed
   * Decryption + decompression performed
   * Original data returned (text or file)

---

## ✨ Features

* 🔐 Strong password-based encryption
* 📉 Compression before embedding (efficient space usage)
* 🎧 WAV-safe LSB embedding (no header corruption)
* 🧪 Corruption & wrong-password detection
* 🌐 Flask-based web UI
* 📂 Supports text **and** file payloads
* 🚫 Rejects unsupported or unsafe files

---

## 🧰 Tech Stack

* **Backend:** Python, Flask
* **Crypto:** `cryptography` (Fernet, PBKDF2HMAC)
* **Audio:** `wave` module
* **Compression:** `zlib`
* **Steganography:** Custom LSB engine

---

## 📁 Project Structure

```
.
├── app.py            # Flask web application
├── steg_engine.py    # Core steganography + crypto engine
├── templates/
│   └── index.html    # Web UI
└── assets/           # Web page screenshot,Sample wave file
```

---

## ⚙️ Installation

```bash
git clone https://github.com/AkhilBangaru/Audio_Steganography.git
cd Audio_Steganography
pip install flask cryptography
python app.py
```

The app runs on:

```
http://127.0.0.1:5000
```

---

## 🚀 Usage

### Encode

1. Upload a `.wav` file
2. Choose payload type (text or file)
3. Enter password
4. Download encoded audio

### Decode

1. Upload encoded `.wav`
2. Enter correct password
3. Get extracted text or file

> **Tip:** a `sample.wav` file is included in this repository for testing.

---

## ⚠️ Limitations

* Only **WAV** audio is supported
* Audio must be large enough to hold payload
* Not designed to bypass forensic analysis
* Educational / controlled-use focus

---

## 🧪 Intended Use

* Learning steganography concepts
* Security research
* Academic projects
* Controlled lab environments

> ❗ Use responsibly. Do not use for unauthorized data hiding.

---

## 👤 Author

**Akhil Bangaru**
Cybersecurity • Applied Cryptography • Offensive & Defensive Research

---
## Web Page

<img width="1171" height="1208" alt="image" src="https://github.com/user-attachments/assets/c33a66bb-fc6f-497f-919f-85d9ad2f96f4" />


## 🛣️ Possible Improvements

* Streaming-safe embedding
* Payload integrity signatures
* Capacity estimation UI
* Dockerized deployment
