# esp32-todo-printer

An asynchronous, modular firmware for the ESP32 designed to bridge digital task management with physical thermal output.

> **⚠️ Project Status: Under Active Development** > This project is currently in the initial architectural implementation phase. Core features are being rolled out following a modular, Single Responsibility design.

## 📋 Overview
The goal of this project is to create a reliable "Physical Todo" station. It receives tasks via a REST API and prints them to a QR203 (TTL) Thermal Printer. Unlike standard "blocking" printer examples, this project uses an asynchronous architecture to ensure the device remains responsive even while printing.

## 🏗 Architecture
The system is built on **ESP-IDF** using **FreeRTOS** to implement a Producer-Consumer pattern.

- **Producers:** API Server task (receives HTTP requests).
- **Queue:** A thread-safe FreeRTOS Job Queue for task orchestration.
- **Consumer:** A Dispatcher task that processes the queue and communicates with the printer.



## 🛠 Planned Core Features
- [ ] **Asynchronous Printing:** Decoupled network and hardware logic.
- [ ] **REST API:** Simple endpoint to receive text-based todos.
- [ ] **Modular Drivers:** Clean separation between UART communication and ESC/POS formatting.
- [ ] **Telegram Integration:** Internal bot task for direct messaging.

## 🔧 Tech Stack
- **Hardware:** ESP32-WROOM-32
- **Printer:** QR203 Thermal Printer (RS232/TTL)
- **Framework:** ESP-IDF v5.x (C/C++)
- **Operating System:** FreeRTOS

## 🚀 Getting Started
*Installation instructions will be provided as the first stable milestone is reached.*

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.