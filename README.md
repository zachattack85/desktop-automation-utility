# Desktop Automation Utility

![Python](https://img.shields.io/badge/Python-3.x-blue)
![License](https://img.shields.io/badge/License-MIT-green)

A configurable hotkey-driven desktop automation utility built in Python.

Supports a toggleable key press loop with adjustable delay, persistent settings,
and audio feedback for activation and deactivation.

Designed to simplify repetitive desktop tasks with a lightweight, hotkey-based workflow.




---

## Screenshot

<p align="center">
  <img src="screenshot.png" width="400"/>
</p>



---

## Features

- Global hotkey to toggle automation on and off  
- Configurable target key and delay (milliseconds)  
- Settings saved to a local configuration file  
- Non-blocking sound feedback on activation and deactivation  
- Simple graphical interface for quick adjustments  

---

## Configuration

- **Target Key** – The key that will be repeatedly pressed
- **Hotkey Combo** – Global shortcut used to toggle automation
- **Delay (ms)** – Time between simulated key presses
- Settings persist between sessions via a local configuration file

---

## Technologies Used

- Python 3  
- Tkinter (GUI)  
- keyboard (global hotkeys)  
- pyautogui (simulated key presses)  
- Pillow (image support for UI)  
- playsound (audio feedback)  

---

## Requirements

- Python 3.9+
- Windows OS (global hotkey functionality requires the `keyboard` library)


---

## Why I Built This

This project was built to explore:
- Global hotkey handling
- GUI application structure with Tkinter
- Background threading for non-blocking execution
- Persistent configuration storage
- Clean separation between UI and automation logic

---

## How to Run

### 1. Clone the repository

```bash
git clone https://github.com/zachattack85/desktop-automation-utility.git
cd desktop-automation-utility
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the application

```bash
python main.py
```

---

## Notes

This tool is intended for personal automation and productivity use.  
Use responsibly and in accordance with the terms of service of any application where automation is applied.

---

## License

This project is licensed under the MIT License.
