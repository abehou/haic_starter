#!/usr/bin/env python3
"""Submit snake code and recording data to GCS"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "eval"))
from snapshot_uploader import SnapshotUploader  # noqa: E402


def load_config(config_path="eval/snapshot_config.json"):
    """Load snapshot config"""
    config_file = Path(config_path)

    if not config_file.exists():
        print("\n" + "=" * 70)
        print("ERROR: Config file not found!")
        print("=" * 70)
        print(f"\nExpected location: {config_path}")
        print("\nTo fix this:")
        print("  1. Check your email for the snapshot_config.json file")
        print(
            "  2. Copy the template: cp eval/snapshot_config.json.template eval/snapshot_config.json"
        )
        print("  3. Paste your config content from the email into the file")
        print("\nOr run ./setup.sh which will guide you through config setup.")
        print("=" * 70 + "\n")
        sys.exit(1)

    try:
        with open(config_file) as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print("\n" + "=" * 70)
        print("ERROR: Invalid JSON in config file!")
        print("=" * 70)
        print(f"\nFile: {config_path}")
        print(f"Error: {e}")
        print("\nTo fix this:")
        print("  1. Check that you copied the ENTIRE JSON from your email")
        print("  2. Make sure there are no extra characters or missing brackets")
        print("  3. Validate your JSON at: https://jsonlint.com/")
        print("=" * 70 + "\n")
        sys.exit(1)

    if not config.get("enabled"):
        print("\n" + "=" * 70)
        print("ERROR: Upload is disabled in config")
        print("=" * 70)
        print(f"\nFile: {config_path}")
        print("\nThe 'enabled' field is set to false.")
        print("This means your config may be a template or incomplete.")
        print("\nTo fix this:")
        print("  1. Make sure you're using the config from your email (not the template)")
        print("  2. Check that 'enabled' is set to true in the JSON")
        print("=" * 70 + "\n")
        sys.exit(1)

    if not config.get("user_id"):
        print("\n" + "=" * 70)
        print("ERROR: user_id not set in config")
        print("=" * 70)
        print(f"\nFile: {config_path}")
        print("\nThe config file is missing the 'user_id' field.")
        print("\nTo fix this:")
        print("  1. Make sure you're using the complete config from your email")
        print("  2. The 'user_id' should be set automatically in the emailed config")
        print("=" * 70 + "\n")
        sys.exit(1)

    return config


def check_recordings_available(data_dir="data"):
    """Check if recording data is available"""
    data_path = Path(data_dir).expanduser()
    if not data_path.exists():
        return False, None

    screenshots_dir = data_path / "screenshots"
    actions_db = data_path / "actions.db"

    if not screenshots_dir.exists() or not actions_db.exists():
        return False, None

    # Count files
    screenshot_files = list(screenshots_dir.glob("*.jpg")) + list(screenshots_dir.glob("*.png"))
    if len(screenshot_files) == 0:
        return False, None

    return True, data_path


def get_recording_summary(data_path):
    """Get summary of recording data"""
    screenshots_dir = data_path / "screenshots"
    actions_db = data_path / "actions.db"
    conversations_file = data_path / "ai_conversations.jsonl"

    screenshot_files = list(screenshots_dir.glob("*.jpg")) + list(screenshots_dir.glob("*.png"))
    num_screenshots = len(screenshot_files)
    db_size_mb = actions_db.stat().st_size / (1024 * 1024)

    has_conversations = conversations_file.exists()
    num_conversations = 0
    if has_conversations:
        with open(conversations_file, "r") as f:
            num_conversations = sum(1 for _ in f)

    total_size = sum(f.stat().st_size for f in screenshot_files) + actions_db.stat().st_size
    if has_conversations:
        total_size += conversations_file.stat().st_size
    total_size_mb = total_size / (1024 * 1024)

    return {
        "num_screenshots": num_screenshots,
        "db_size_mb": db_size_mb,
        "has_conversations": has_conversations,
        "num_conversations": num_conversations,
        "total_size_mb": total_size_mb,
    }


def upload_recordings(data_path, config, auto_delete=False):
    """Upload recording data"""
    from gum.gcs_uploader import GCSUploader

    uploader = GCSUploader(config.get("config_path", "eval/snapshot_config.json"))

    if not uploader.enabled:
        print("\n[!] Recording upload skipped (not enabled in config)")
        return {"status": "disabled"}

    print(f"\n{'='*70}")
    print("UPLOADING RECORDINGS")
    print(f"{'='*70}")

    result = uploader.upload_recording(str(data_path))

    if result["status"] == "success":
        print(f"[OK] Recordings uploaded to slot {result.get('slot', 'N/A')}")

        # Auto-delete if requested
        if auto_delete:
            print("\nCleaning up local recording data...")
            import shutil

            screenshots_dir = data_path / "screenshots"
            actions_db = data_path / "actions.db"
            conversations_file = data_path / "ai_conversations.jsonl"

            shutil.rmtree(screenshots_dir)
            actions_db.unlink()
            for wal_file in data_path.glob("actions.db-*"):
                wal_file.unlink()
            if conversations_file.exists():
                conversations_file.unlink()
            print("[OK] Local recording data deleted")
        else:
            print(f"\nLocal data preserved in: {data_path}")

        print(f"{'='*70}")
        return result

    elif result["status"] == "error":
        error_msg = result.get("error", "")
        print(f"\n[X] Recording upload failed: {error_msg}")

        # Check for common error patterns and provide helpful guidance
        if "403" in error_msg or "Forbidden" in error_msg or "AccessDenied" in error_msg:
            print("\n" + "-" * 70)
            print("This error often means your upload URLs have EXPIRED.")
            print("URLs are valid for 7 days from when they were generated.")
            print("\nTo fix this:")
            print("  Contact the study coordinators to request new credentials.")
            print("-" * 70)
        elif "400" in error_msg or "Bad Request" in error_msg:
            print("\n" + "-" * 70)
            print("This may indicate a problem with the upload URL format.")
            print("\nTo fix this:")
            print("  1. Check that your config file has valid URLs")
            print("  2. Re-copy the config from your email if needed")
            print("-" * 70)
        elif "timeout" in error_msg.lower() or "connection" in error_msg.lower():
            print("\n" + "-" * 70)
            print("Network error - please check your internet connection and try again.")
            print("-" * 70)

        print(f"{'='*70}")
        return result
    else:
        print(f"[!] Unexpected status: {result.get('status')}")
        return result


def submit_snake(args, config):
    """Submit snake code and automatically submit recordings if available"""
    # Validate source
    source_path = Path(args.source)
    if not source_path.exists():
        print("\n" + "=" * 70)
        print("ERROR: Snake source directory not found!")
        print("=" * 70)
        print(f"\nExpected location: {args.source}")
        print("\nTo fix this:")
        print("  1. Make sure your snake code is in the 'your_snake/' directory")
        print("  2. If your snake is in a different directory, use --source YOUR_DIR")
        print("\nExample:")
        print("  python submit.py -s init --snake_name my_snake --source your_snake")
        print("=" * 70 + "\n")
        return 1

    # Check for recordings
    has_recordings, data_path = check_recordings_available(args.data_dir)
    recording_summary = None
    if has_recordings:
        recording_summary = get_recording_summary(data_path)

    # Show combined submission info
    print(f"\n{'='*70}")
    print("SUBMISSION")
    print(f"{'='*70}")
    print(f"User:   {config['user_id']}")
    print(f"Stage:  {args.stage}")
    print("\nSnake Code:")
    print(f"  Name:   {args.snake_name}")
    print(f"  Source: {args.source}")

    if has_recordings:
        print("\nRecording Data:")
        print(f"  Screenshots:      {recording_summary['num_screenshots']} files")
        print(f"  Database:         {recording_summary['db_size_mb']:.1f} MB")
        if recording_summary["has_conversations"]:
            print(f"  AI Conversations: {recording_summary['num_conversations']} entries")
        print(f"  Total size:       {recording_summary['total_size_mb']:.1f} MB")
    else:
        print(f"\n[!] No recording data found in {args.data_dir}")
        print("  (Recording upload will be skipped)")

    print(f"{'='*70}\n")

    response = (
        input("Submit snake code" + (" and recordings" if has_recordings else "") + "? [y/N]: ")
        .strip()
        .lower()
    )
    if response not in ["y", "yes"]:
        print("Cancelled")
        return 0

    print()

    # Step 1: Upload snake code
    print(f"{'='*70}")
    print("UPLOADING SNAKE CODE")
    print(f"{'='*70}")

    uploader = SnapshotUploader(config)
    tarball, metadata = uploader.create_snapshot(
        args.source, args.stage, results_data={"stage": args.stage, "snake_name": args.snake_name}
    )

    result = uploader.upload(tarball, metadata, args.stage)

    tarball.unlink()
    metadata.unlink()

    if result["status"] != "success":
        print(f"[X] Snake code upload failed: {result.get('error')}")
        print(f"{'='*70}")
        return 1

    print("[OK] Snake code uploaded successfully")
    print(f"{'='*70}")

    # Step 2: Upload recordings (if available)
    recording_result = None
    if has_recordings:
        recording_result = upload_recordings(data_path, config, auto_delete=args.delete_local)

    # Final summary
    print(f"\n{'='*70}")
    print("[OK] SUBMISSION COMPLETE")
    print(f"{'='*70}")
    print(f"[OK] Snake code:  {args.stage} stage")
    if has_recordings:
        if recording_result and recording_result["status"] == "success":
            print("[OK] Recordings:  uploaded")
        else:
            print("[!] Recordings:  failed or disabled")
    else:
        print("Recordings:  none available")
    print(f"{'='*70}")

    return 0


def submit_recordings_only(args, config):
    """Submit only recording data (standalone mode)"""

    # Validate data directory
    data_path = Path(args.data_dir).expanduser()
    if not data_path.exists():
        print("\n" + "=" * 70)
        print("ERROR: Recording data directory not found!")
        print("=" * 70)
        print(f"\nExpected location: {args.data_dir}")
        print("\nTo fix this:")
        print("  1. Run 'gum' to start recording your development session")
        print("  2. Recording data will be saved to data/")
        print("  3. After recording, run this command again to submit")
        print("\nIf your data is in a different location, use --data-dir:")
        print("  python submit.py --recordings-only --data-dir /path/to/data")
        print("=" * 70 + "\n")
        return 1

    screenshots_dir = data_path / "screenshots"
    actions_db = data_path / "actions.db"

    if not screenshots_dir.exists():
        print("\n" + "=" * 70)
        print("ERROR: Screenshots directory not found!")
        print("=" * 70)
        print(f"\nExpected: {screenshots_dir}")
        print("\nThis usually means:")
        print("  1. Recording hasn't been started yet (run 'gum' first)")
        print("  2. Recording was stopped before any screenshots were taken")
        print("  3. The data directory path is incorrect")
        print("=" * 70 + "\n")
        return 1

    if not actions_db.exists():
        print("\n" + "=" * 70)
        print("ERROR: Actions database not found!")
        print("=" * 70)
        print(f"\nExpected: {actions_db}")
        print("\nThis usually means the recording session didn't complete properly.")
        print("Try running 'gum' again to create a new recording session.")
        print("=" * 70 + "\n")
        return 1

    # Get summary
    summary = get_recording_summary(data_path)

    # Show summary
    print(f"\n{'='*70}")
    print("RECORDING DATA SUBMISSION")
    print(f"{'='*70}")
    print(f"User:               {config['user_id']}")
    print(f"Data directory:     {data_path}")
    print(f"Screenshots:        {summary['num_screenshots']} files")
    print(f"Database:           {summary['db_size_mb']:.1f} MB")
    if summary["has_conversations"]:
        print(f"AI Conversations:   {summary['num_conversations']} entries")
    print(f"Total size:         {summary['total_size_mb']:.1f} MB")
    print(f"{'='*70}\n")

    # Confirm
    response = input("Submit recordings to GCS? [y/N]: ").strip().lower()
    if response not in ["y", "yes"]:
        print("Cancelled")
        print("\nTip: Review screenshots first with: python review_recording.py")
        return 0

    print()

    # Upload
    result = upload_recordings(data_path, config, auto_delete=args.delete_local)

    if result["status"] == "success":
        return 0
    elif result["status"] == "error":
        return 1
    else:
        return 1


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Submit snake code (with recordings) or recordings only",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Submit initial snake code + recordings (simple form)
  python submit.py -s init --snake_name my_snake

  # Submit final snake code + recordings and delete local data
  python submit.py -s final --snake_name my_snake_v2 --delete-local

  # Submit only recordings (without snake code)
  python submit.py --recordings-only
        """,
    )

    # Main arguments for snake submission
    parser.add_argument(
        "-s",
        "--stage",
        choices=["init", "final"],
        help="Submission stage (triggers snake + recordings submission)",
    )
    parser.add_argument("--snake_name", help="Name of your snake (required with -s/--stage)")
    parser.add_argument(
        "--source", default="your_snake", help="Source directory (default: your_snake)"
    )

    # Recordings-only mode (mutually exclusive with snake submission)
    parser.add_argument(
        "--recordings-only", action="store_true", help="Submit only recording data (no snake code)"
    )

    # Common arguments
    parser.add_argument(
        "--data-dir", default="data", help="Recording data directory (default: data)"
    )
    parser.add_argument("--config", default="eval/snapshot_config.json", help="Config file path")
    parser.add_argument(
        "--delete-local",
        action="store_true",
        help="Delete local recording data after successful upload",
    )

    args = parser.parse_args()

    # Load config (needed for all modes)
    config = load_config(args.config)
    config["config_path"] = args.config

    # Determine mode based on arguments
    if args.recordings_only:
        # Recordings-only mode
        if args.stage or args.snake_name:
            parser.error("--recordings-only cannot be used with -s/--stage or --snake_name")
        return submit_recordings_only(args, config)

    elif args.stage or args.snake_name:
        # Snake submission mode (with recordings)
        if not args.stage:
            parser.error("--snake_name requires -s/--stage")
        if not args.snake_name:
            parser.error("-s/--stage requires --snake_name")
        return submit_snake(args, config)

    else:
        # No mode specified
        parser.print_help()
        print("\nError: Must specify either:")
        print("  1. Snake submission: -s/--stage and --snake_name")
        print("  2. Recordings only: --recordings-only")
        return 1


if __name__ == "__main__":
    sys.exit(main())
