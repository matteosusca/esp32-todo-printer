# 📄 Documento di Progetto: ESP32 Smart Thermal Printer

## 1. Visione Generale

Il progetto consiste nella realizzazione di una stampante termica intelligente ed espandibile basata su ESP32. Il dispositivo permette di stampare biglietti, ToDo list (a breve e lungo termine) e appunti generici ricevuti tramite Telegram (o altre fonti future), applicando formattazioni e stili specifici. Il sistema è progettato per operare inizialmente in modalità *standalone* (tutta la logica sull'ESP32), ma l'architettura a interfacce garantisce una facile migrazione verso un modello *client-server* in futuro.

## 2. Contesto Hardware

* **Microcontrollore:** ESP32-S3 WROOM-1 N16R8
* *Vantaggi:* Dotato di 16MB di Flash e 8MB di PSRAM. Questa enorme quantità di RAM esterna elimina quasi del tutto i rischi di `MemoryError` durante il parsing di JSON complessi o l'elaborazione di immagini.


* **Stampante:** QR203 (Mini Embedded Thermal Printer)
* *Specifiche:* Carta da 58mm, risoluzione 384 punti/riga, protocollo Seriale ESC/POS.
* **Vincolo Elettrico Critico:** Richiede alimentazione dedicata (5V-9V, almeno 2A). **Non** deve essere alimentata direttamente dal pin 5V dell'ESP32 quando collegato via USB, pena il danneggiamento della scheda. Necessita di masse (GND) in comune.



## 3. Requisiti del Sistema

### Requisiti Funzionali (RF)

* **RF1 - Acquisizione Dati:** Ricezione asincrona di note tramite *Long Polling* da bot Telegram.
* **RF2 - Categorizzazione:** Supporto per diverse tipologie di note (Short-term ToDo, Long-term/Ideas, Misc/Immagini).
* **RF3 - Formattazione:** Le note contengono titolo, descrizione e scadenza opzionale. Supporto per sintassi Markdown di base e inserimento di divisori/cornici.
* **RF4 - Grafica:** Capacità di renderizzare immagini in formato bitmap a 1-bit (bianco e nero/dithering).
* **RF5 - Buffer (Futuro):** Predisposizione per sincronizzazione con database esterni (es. Notion) per tracciare lo stato di stampa.

### Requisiti Non Funzionali (RNF)

* **RNF1 - Architettura Modulare:** Separazione netta tra ricezione, logica di business, rendering e interazione hardware.
* **RNF2 - Scalabilità tramite Builder:** Utilizzo di un pattern *Builder/DSL* per l'assemblaggio del sistema, permettendo la sostituzione trasparente dei moduli (es. passare da un rendering locale a uno remoto).
* **RNF3 - Backpressure:** Implementazione di un sistema a code per disaccoppiare la ricezione dei messaggi (veloce) dalla stampa fisica (lenta).
* **RNF4 - Gestione Risorse:** Nonostante l'ampia RAM (PSRAM), l'architettura favorirà l'uso di stream/generatori per il rendering, mantenendo il sistema reattivo.

## 4. Architettura Logica (Data Pipeline)

Il sistema è basato su un flusso dati unidirezionale (Pipeline).

```text
[Telegram / Sorgente]
       │
       ▼ (Long Polling)
┌─────────────────────────┐
│     Note Listener       │ Intercetta i dati e genera una RawNote.
└──────────┬──────────────┘
           │
           ▼ (Oggetto: RawNote)
┌─────────────────────────┐
│      Dispatcher         │ Analizza metadati e smista al Drawer corretto.
└────┬───────────┬────────┘
     │           │
     ▼           ▼ 
┌─────────┐ ┌─────────┐
│ Drawer  │ │ Drawer  │ Renderizza testo/immagini (tramite Yield/Generatori)
│ (Cat A) │ │ (Cat B) │ e produce i comandi raw (ESC/POS).
└────┬────┘ └────┬────┘
     │           │
     ▼           ▼ (Oggetto: PrintJob)
┌─────────────────────────┐
│     Coda (Queue)        │ Bufferizza i PrintJob (FIFO) per evitare blocchi.
└──────────┬──────────────┘
           │
           ▼ 
┌─────────────────────────┐
│     Print Worker        │ Estrae dalla coda, invia i byte via Seriale
└──────────┬──────────────┘ all'hardware rispettando i tempi della stampante.
           │
           ▼ (Seriale TX/RX)
  [Stampante QR203]

```

## 5. Scelte Tecnologiche

1. **Linguaggio e Core:** **MicroPython** (ideale per l'hardware selezionato, veloce e moderno).
2. **Concorrenza:** Modulo **`uasyncio`** per gestire simultaneamente l'ascolto della rete (Listener) e la stampa (Worker) senza bloccare il microcontrollore.
3. **Elaborazione Dati:** Utilizzo di **Generatori (`yield`)** nei *Drawer* per calcolare e inviare i dati grafici alla stampante riga per riga, ottimizzando il flusso.
4. **Protocollo di Stampa:** Generazione di comandi **ESC/POS** customizzati in Python per interagire con la stampante via UART.

## 6. Struttura del Progetto (File System)

```text
/
├── main.py               # Punto di ingresso: AppBuilder e Avvio dell'Event Loop
├── boot.py               # Setup iniziale a basso livello (Wi-Fi, Mount file system)
├── config.json           # Credenziali (SSID, Password, Telegram Token)
│
├── /core
│   ├── app.py            # Gestione della Coda e del Loop di uasyncio
│   └── models.py         # Definizione dei Data Transfer Object (RawNote, PrintJob)
│
├── /listeners
│   ├── base.py           # Interfaccia astratta Listener
│   └── telegram.py       # Implementazione Long Polling
│
├── /drawers
│   ├── base.py           # Interfaccia astratta Drawer
│   ├── short_term.py     # Logica di layout per le liste ToDo
│   └── misc.py           # Logica di layout per appunti liberi/immagini
│
└── /hardware
    ├── escpos.py         # Utility per la conversione testo/immagini in byte ESC/POS
    └── printer.py        # Interazione con pin UART e controllo di flusso HW

```