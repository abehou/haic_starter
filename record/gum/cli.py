from dotenv import load_dotenv

load_dotenv()

import argparse  # noqa: E402
import asyncio  # noqa: E402
import os  # noqa: E402
import platform  # noqa: E402
import sys  # noqa: E402
import signal  # noqa: E402
from gum import gum  # noqa: E402
from gum.observers import (  # noqa: E402
    Screen,
    AIActivityDetector,
    ConversationObserver,
    TerminalObserver,
)

# Windows-specific setup
if sys.platform == "win32":
    # Allow Ctrl+C to work in Windows terminal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Enable DPI awareness for correct window coordinates with display scaling
    # This must be called before any GUI/window operations
    try:
        import ctypes

        # SetProcessDpiAwareness: 2 = Per-Monitor DPI Aware
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        try:
            # Fallback for older Windows versions
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass


def parse_args():
    parser = argparse.ArgumentParser(
        description="GUM - A Python package with command-line interface"
    )
    parser.add_argument(
        "--user-name", "-u", type=str, default="anonymous", help="The user name to use"
    )
    parser.add_argument("--debug", "-d", action="store_true", help="Enable debug mode")

    # Scroll filtering options
    parser.add_argument(
        "--scroll-debounce",
        type=float,
        default=1.0,
        help="Minimum time between scroll events (seconds, default: 1.0)",
    )
    parser.add_argument(
        "--scroll-min-distance",
        type=float,
        default=5.0,
        help="Minimum scroll distance to log (pixels, default: 5.0)",
    )
    parser.add_argument(
        "--scroll-max-frequency",
        type=int,
        default=10,
        help="Maximum scroll events per second (default: 10)",
    )
    parser.add_argument(
        "--scroll-session-timeout",
        type=float,
        default=2.0,
        help="Scroll session timeout (seconds, default: 2.0)",
    )

    parser.add_argument(
        "--screenshots-dir",
        type=str,
        default="data/screenshots",
        help="Directory to save screenshots (default: data/screenshots)",
    )

    # Region specification
    parser.add_argument(
        "--region",
        type=str,
        default=None,
        help='Capture region as "left,top,width,height" (e.g., "0,0,1920,1080"). '
        "If not specified, will prompt for interactive selection.",
    )
    parser.add_argument(
        "--fullscreen",
        action="store_true",
        help="Capture full screen without prompting for region selection",
    )
    parser.add_argument(
        "--terminal-only",
        action="store_true",
        help="Terminal recording only - skip GUI/screenshot capture (auto-enabled on Wayland)",
    )

    # Inactivity timeout
    parser.add_argument(
        "--inactivity-timeout",
        type=float,
        default=45,
        help="Stop recording after N minutes of inactivity (default: 45)",
    )

    # AI monitoring options
    parser.add_argument(
        "--monitor-ai",
        action="store_true",
        default=True,
        help="Monitor AI tool usage (ChatGPT, Claude, Cursor, etc.)",
    )

    return parser.parse_args()


async def _main():
    args = parse_args()

    # Configure logging based on debug flag
    import logging

    if args.debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S",
        )
    else:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # Auto-detect Wayland and enable terminal-only mode if not explicitly disabled
    is_wayland = os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"

    if is_wayland and not args.terminal_only:
        # Check if user explicitly requested GUI capture
        if args.region or args.fullscreen:
            # User explicitly wants GUI capture, respect that
            print("\n" + "=" * 70)
            print("[!] WAYLAND DETECTED - GUI CAPTURE MAY BE LIMITED")
            print("=" * 70)
            print("Wayland restricts screen capture for security.")
            print("You may experience issues with screenshot capture.")
            print("\nTip: Use --terminal-only for better reliability")
            print("=" * 70 + "\n")
        else:
            # Auto-enable terminal-only mode on Wayland
            print("\n" + "=" * 70)
            print("WAYLAND DETECTED - AUTO-ENABLING TERMINAL-ONLY MODE")
            print("=" * 70)
            print("Wayland restricts GUI/screenshot capture for security.")
            print("Automatically switching to terminal-only mode for best results.")
            print("\nTo force GUI capture anyway, use:")
            print("  gum --fullscreen    (force full-screen capture)")
            print("  gum --region X,Y,W,H (force region capture)")
            print("=" * 70 + "\n")
            args.terminal_only = True

    print(f"User Name: {args.user_name}")
    # Display warning message before starting recording
    print("\n" + "=" * 70)
    print("[!] BEFORE YOU BEGIN RECORDING")
    print("=" * 70)
    print("\nPlease make sure your workspace is clean and contains only")
    print("study-related materials.")
    print("\nClose all personal tabs, folders, and unrelated applications.")
    print("\nOnly the window you select will be recorded - activity outside")
    print("it will be ignored.")
    print("\nYou can pause or stop recording at any time using Ctrl + C")
    print("in the terminal.")
    print(f"\nRecording will automatically stop after {args.inactivity_timeout} minutes")
    print("of inactivity in the selected window.")
    print("\nWhen finished, review your recording and delete anything you")
    print("don't want to share.")
    print("\n" + "=" * 70)

    # Wait for user confirmation
    input("\nPress Enter to confirm and start recording...")
    print("\n" + "=" * 70)
    print("INITIALIZING RECORDING...")
    print("=" * 70)
    print("[1/5] Setting up data directory...")

    # Use data directory for database, screenshots go in data/screenshots
    # Use absolute path to ensure consistency regardless of where script is run from
    import pathlib

    # Find project root: go up 3 levels from record/gum/cli.py -> record/gum/ -> record/ -> project root
    project_root = pathlib.Path(__file__).parent.parent.parent
    data_directory = str(project_root / "data")
    
    # Convert screenshots_dir to absolute path relative to project root if it's relative
    screenshots_dir = args.screenshots_dir
    if not os.path.isabs(screenshots_dir):
        screenshots_dir = str(project_root / screenshots_dir)

    # Collect all observers
    observers = []
    print("[2/5] Initializing screen capture...")

    # Only create Screen observer if not in terminal-only mode
    if not args.terminal_only:
        # Parse region coordinates if provided
        target_coordinates = None
        if args.region:
            try:
                parts = [int(x.strip()) for x in args.region.split(",")]
                if len(parts) != 4:
                    raise ValueError("Region must have exactly 4 values: left,top,width,height")
                target_coordinates = tuple(parts)
                print(f"Using specified region: {target_coordinates}")
            except ValueError as e:
                print(f"Error parsing --region: {e}")
                print("Region format should be: left,top,width,height (e.g., 0,0,1920,1080)")
                return
        elif args.fullscreen:
            # Will trigger full-screen capture in Screen observer
            print("Using full-screen capture mode")
            # Leave target_coordinates as None, Screen will handle it
        else:
            print("      Please select the window/region to record...")

        # Create Screen observer with scroll filtering configuration
        screen_observer = Screen(
            screenshots_dir=screenshots_dir,
            debug=args.debug,
            scroll_debounce_sec=args.scroll_debounce,
            scroll_min_distance=args.scroll_min_distance,
            scroll_max_frequency=args.scroll_max_frequency,
            scroll_session_timeout=args.scroll_session_timeout,
            inactivity_timeout=args.inactivity_timeout * 60,  # Convert minutes to seconds
            target_coordinates=target_coordinates,
        )
        observers.append(screen_observer)
        print("      Screen capture initialized successfully")
    else:
        print("      Skipping (terminal-only mode)")

    print("[3/5] Initializing terminal monitoring...")

    # Add terminal observer for headless mode (when input monitoring is unavailable)
    # Check if we're in headless mode by testing pynput
    try:
        pass

        # pynput available, input monitoring should work
    except (ImportError, Exception) as e:
        # pynput unavailable, likely headless mode
        str(e)
    # Enable TerminalObserver for all platforms to capture terminal/AI CLI activity
    # macOS uses 'ps' command, Linux uses /proc, Windows uses PowerShell/WMI
    is_macos = platform.system() == "Darwin"  # noqa: F841
    is_windows = platform.system() == "Windows"  # noqa: F841
    _ = platform.system() == "Linux"  # is_linux - not used currently
    # Enable TerminalObserver for ALL platforms (headless, macOS, Windows, Linux)
    # This captures terminal commands and AI CLI tools on all systems
    if True:  # Always enable terminal monitoring
        terminal_observer = TerminalObserver(
            poll_interval=2.0,
            screenshots_dir=screenshots_dir,  # Pass screenshots dir so AI logs are saved there
            debug=args.debug,
        )
        observers.append(terminal_observer)
        if is_windows:
            print("      Terminal monitoring initialized (Windows/PowerShell)")
        elif is_macos:
            print("      Terminal monitoring initialized (macOS/ps)")
        elif pathlib.Path("/proc").exists():
            print("      Terminal monitoring initialized (Linux/proc)")
        else:
            print("      Terminal monitoring initialized (bash history fallback)")

    # Add AI monitoring if requested
    if args.monitor_ai:
        print("[4/5] Initializing AI activity monitoring...")
        ai_detector = AIActivityDetector(
            screenshots_dir=screenshots_dir,
            poll_interval=0.5,
            debug=args.debug,
            data_directory=data_directory,
        )
        observers.append(ai_detector)

        # Conversation Observer for detailed event-based capture
        conversation_observer = ConversationObserver(
            screenshots_dir=screenshots_dir, data_directory=data_directory, debug=args.debug
        )
        observers.append(conversation_observer)
        print("      AI monitoring initialized (ChatGPT, Claude, Cursor, etc.)")
    else:
        print("[4/5] AI monitoring... skipped (disabled)")

    print("[5/5] Starting recording engine...")

    # Create a stop event for graceful shutdown
    stop_event = asyncio.Event()

    # Set up signal handlers for graceful shutdown
    def signal_handler():
        stop_event.set()

    # On Windows, we need special handling
    if sys.platform == "win32":
        # Use a different approach for Windows - check for keyboard interrupt periodically
        async def wait_for_stop():
            while not stop_event.is_set():
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=0.5)
                except asyncio.TimeoutError:
                    pass

    else:
        # On Unix, we can use signal handlers
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, signal_handler)

        async def wait_for_stop():
            await stop_event.wait()

    try:
        async with gum(args.user_name, *observers, data_directory=data_directory):
            print("\n" + "=" * 70)
            print("RECORDING IN PROGRESS")
            print("=" * 70)
            print("Press Ctrl+C to stop recording...")
            print("=" * 70 + "\n")

            await wait_for_stop()
    except KeyboardInterrupt:
        pass
    except asyncio.CancelledError:
        pass
    finally:
        # Give observers time to clean up
        try:
            await asyncio.sleep(0.1)
        except Exception:
            pass

        print("\n\n" + "=" * 70)
        print("Recording stopped")
        print("=" * 70)
        print(f"\nData saved in: {data_directory}/")
        print("\nNext steps:")
        print("  1. Review recording:  python review_recording.py")
        print("  2. Submit to GCS:     python submit.py")
        print("=" * 70)


def main():
    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        # This is expected - user pressed Ctrl+C
        pass
    except Exception as e:
        import logging

        logging.error(f"Unexpected error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
