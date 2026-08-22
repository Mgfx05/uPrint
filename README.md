# ERB-APP
# 🖨️ ERB — Easy Print & Collect

<p align="center">

  <img src="https://img.shields.io/badge/Status-In%20Development-orange?style=for-the-badge">
  <img src="https://img.shields.io/badge/Python-FastAPI-blue?style=for-the-badge">
  <img src="https://img.shields.io/badge/Frontend-HTML%20%7C%20CSS%20%7C%20JavaScript-purple?style=for-the-badge">
  <img src="https://img.shields.io/badge/Database-SQLite-green?style=for-the-badge">
  <img src="https://img.shields.io/badge/Hardware-Raspberry%20Pi-red?style=for-the-badge">

</p>

<p align="center">
  <b>Upload. Customize. Print. Collect.</b>
</p>

---

## 📌 About

**ERB (Easy Print & Collect)** is a smart document-printing platform designed to make printing documents simple and convenient.

Users can upload PDF documents, select printing options, choose the number of copies, view the calculated price, and place a printing order.

The long-term goal of ERB is to connect the web platform with a **Raspberry Pi controlled physical printer**, creating an automated print-and-collect system.

---

## ✨ Current Features

### 📄 PDF Upload

- Upload PDF documents
- Store uploaded files on the backend
- Automatically detect PDF page count
- Generate a unique file ID
- Display file information to the user

### 🖨️ Printing Options

Currently supported:

| Option | Price |
|--------|-------|
| B&W | ₹2 / page |
| Color | ₹10 / page |

### 📑 Copies

Users can select the number of copies.

Current range:

```text
1 – 50 copies
