---
name: project-architecture
description: Active when designing, writing, editing, or refactoring the ESP32 Smart Thermal Printer architecture, modular components, or implementing modules under core/, listeners/, drawers/, or hardware/ directories.
activation: model-decision
---

# ESP32 Smart Thermal Printer Project Architecture & Context

## 1. Project Vision
We are building a smart, modular thermal printer powered by an ESP32 microcontroller using MicroPython. The device receives notes, to-do lists, and images via Telegram (Long Polling) and prints them using specific formatting rules.
The architecture is designed to be standalone for now, but strictly modular (using a Builder/Pipeline pattern) to easily scale into a client-server architecture in the future.

## 2. System Requirements

### Functional Requirements (RF)
* **RF1 - Data Acquisition:** Asynchronous note reception via Telegram Bot Long Polling.
* **RF2 - Categorization:** Support for different note types (Short-term ToDo, Long-term/Ideas, Misc/Images).
* **RF3 - Formatting:** Notes contain title, description, and optional deadline. Support for basic Markdown syntax and custom dividers/borders.
* **RF4 - Graphics:** Capability to render 1-bit bitmap images (black & white/dithered).
* **RF5 - Buffer (Future):** Support for synchronization with external databases (e.g., Notion) to track print status.

### Non-Functional Requirements (RNF)
* **RNF1 - Modular Architecture:** Clear separation between data source (listeners), business logic, formatting/rendering (drawers), and hardware interaction.
* **RNF2 - Scalability via Builder:** Use a Builder/DSL pattern to assemble the system, allowing easy component swap (e.g., local vs remote rendering).
* **RNF3 - Backpressure Handling:** Use an asynchronous FIFO queue to buffer print jobs, decoupling data reception (fast) from physical printing (slow).
* **RNF4 - Resource Management:** Use streams and Python Generators (`yield`) in Drawers to calculate and stream printer bytes row-by-row, maintaining a small memory footprint.

## 3. Logical Architecture & Data Pipeline
The software follows a strictly unidirectional pipeline operating asynchronously using `uasyncio`:

```text
[Telegram / Source]
       │
       ▼ (Long Polling)
┌─────────────────────────┐
│     Note Listener       │ Intercepts data and generates a RawNote DTO.
└──────────┬──────────────┘
           │
           ▼ (Object: RawNote)
┌─────────────────────────┐
│      Dispatcher         │ Analyzes metadata and routes the RawNote to the correct Drawer.
└────┬───────────┬────────┘
     │           │
     ▼           ▼ 
┌─────────┐ ┌─────────┐
│ Drawer  │ │ Drawer  │ Formats/renders content using Generators (yield)
│ (Cat A) │ │ (Cat B) │ to produce raw ESC/POS command bytes.
└────┬────┘ └────┬────┘
     │           │
     ▼           ▼ (Object: PrintJob)
┌─────────────────────────┐
│     Coda (Queue)        │ Buffers PrintJobs (FIFO) to prevent blocking.
└──────────┬──────────────┘
           │
           ▼ 
┌─────────────────────────┐
│     Print Worker        │ Dequeues PrintJobs and sends bytes over UART to the
└──────────┬──────────────┘ printer, handling timing and flow control.
           │
           ▼ (Serial TX/RX)
  [QR203 Printer]
```

## 4. Technology Stack & Choices
1. **Core Language:** MicroPython.
2. **Concurrency:** `uasyncio` for non-blocking networking and printer tasks.
3. **Data Processing:** Generators (`yield`) in Drawers to render and stream image/text data row-by-row.
4. **Print Protocol:** Custom ESC/POS command generator implemented in Python.

## 5. Target Directory & File Structure
```text
/
├── config.json           # Credentials (SSID, Password, Telegram Token)
├── boot.py               # Runs first: Network setup and low-level init
├── main.py               # Entry point: AppBuilder and uasyncio Event Loop
│
├── /core
│   ├── app.py            # Manages the Queue and uasyncio Pipeline tasks
│   └── models.py         # Data Transfer Objects (RawNote, PrintJob)
│
├── /listeners
│   ├── base.py           # Abstract BaseListener interface
│   └── telegram.py       # Async Long Polling implementation
│
├── /drawers
│   ├── base.py           # Abstract BaseDrawer interface
│   ├── short_term.py     # Layout logic for ToDo lists
│   └── misc.py           # Layout logic for free text/images
│
└── /hardware
    ├── escpos.py         # Utilities for text/image to ESC/POS byte conversion
    └── printer.py        # UART interaction, flow control, and PrintWorker task
```
