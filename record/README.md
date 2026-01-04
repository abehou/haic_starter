# Human Activity Recording Tool

## Installation

Install from source with platform-specific dependencies:

### Windows

```bash
# Install with Windows-specific dependencies for window detection
pip install -e .[windows]
```

This installs:
- `pywin32` - Required for detecting active windows via Windows API
- `psutil` - Required for process information
- `uiautomation` - Optional, for enhanced browser tab detection

### macOS

```bash
pip install -e .
```

Make sure to enable recording permissions: go to System Preferences -> Privacy & Security -> Accessibility, and allow recording for the app you use to edit code (e.g., VSCode or Terminal).

### Linux

First, install build tools, GUI libraries, GObject dependencies, window management tools, and screenshot utilities:

```bash
# On Arch Linux:
sudo pacman -S base-devel gcc python tk gobject-introspection gtk3 cairo python-cairo wmctrl maim

# On Debian/Ubuntu:
sudo apt-get install build-essential python3-dev python3-tk \
    libgirepository1.0-dev libcairo2-dev pkg-config \
    python3-gi python3-gi-cairo gir1.2-gtk-3.0 \
    wmctrl xdotool maim

# On Fedora/RHEL:
sudo dnf install gcc python3-devel python3-tkinter \
    gobject-introspection-devel cairo-devel pkg-config \
    python3-gobject gtk3 wmctrl xdotool maim
```

**Note:**
- `wmctrl` (or `xdotool`) is required for window selection on X11
- `maim` is required for screenshot capture on X11 (thread-safe, works reliably in VMs)

Then install with Linux-specific dependencies:

```bash
# Option 1: Install with Linux extras (includes PyGObject, python-xlib, ewmh)
pip install -e .[linux]

# Option 2: If PyGObject installation fails, install without Linux extras
# pip install -e .
```

**Note:** PyGObject is used for Wayland portal integration. If you're on X11 or encounter installation issues, you can use Option 2.

### Optional: Memory Monitoring

For memory monitoring capabilities on any platform:
```bash
pip install -e .[monitoring]
```

## Usage

```bash
gum
```

The recorded actions and screenshots will be saved in `data/` at the project root.

### Scroll Filtering Options

To reduce unnecessary scroll logging, you can configure scroll filtering parameters:

```bash
# More aggressive filtering (fewer scroll events logged)
gum --scroll-debounce 1.0 \
    --scroll-min-distance 10.0 \
    --scroll-max-frequency 5 \
    --scroll-session-timeout 3.0

# Less filtering (more scroll events logged)
gum --scroll-debounce 0.2 \
    --scroll-min-distance 2.0 \
    --scroll-max-frequency 20 \
    --scroll-session-timeout 1.0
```

**Scroll filtering parameters:**
- `--scroll-debounce`: Minimum time between scroll events (default: 0.5 seconds)
- `--scroll-min-distance`: Minimum scroll distance to log (default: 5.0 pixels)
- `--scroll-max-frequency`: Maximum scroll events per second (default: 10)
- `--scroll-session-timeout`: Scroll session timeout (default: 2.0 seconds)