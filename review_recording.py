#!/usr/bin/env python3
"""
Interactive web viewer to review and clean up recordings before submission.
Users can navigate through screenshots and delete unwanted ones.
"""
import sqlite3
from pathlib import Path
from flask import Flask, render_template, jsonify, send_from_directory

app = Flask(__name__)

# Global state - use absolute path relative to this script
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / "data"
SCREENSHOTS_DIR = DATA_DIR / "screenshots"
DB_PATH = DATA_DIR / "actions.db"


def get_screenshot_list():
    """Get sorted list of screenshot files"""
    if not SCREENSHOTS_DIR.exists():
        return []

    screenshots = sorted(SCREENSHOTS_DIR.glob("*.jpg"), key=lambda p: p.stat().st_mtime)
    return [s.name for s in screenshots]


def get_action_for_screenshot(screenshot_name):
    """Get the action associated with a screenshot from the database"""
    if not DB_PATH.exists():
        return None

    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # Find observation that mentions this screenshot
        cursor.execute(
            "SELECT content, created_at FROM observations WHERE content LIKE ? ORDER BY created_at LIMIT 1",
            (f"%{screenshot_name}%",),
        )
        result = cursor.fetchone()
        conn.close()

        if result:
            return {"action": result[0], "timestamp": result[1]}
    except Exception:
        pass

    return None


@app.route("/")
def index():
    """Main viewer page"""
    screenshots = get_screenshot_list()
    total_size = sum((SCREENSHOTS_DIR / s).stat().st_size for s in screenshots) / (1024 * 1024)

    return render_template(
        "review.html", total_screenshots=len(screenshots), total_size_mb=f"{total_size:.1f}"
    )


@app.route("/api/screenshots")
def list_screenshots():
    """API: Get list of all screenshots"""
    screenshots = get_screenshot_list()

    # Get file info
    screenshot_data = []
    for name in screenshots:
        path = SCREENSHOTS_DIR / name
        action = get_action_for_screenshot(name)

        screenshot_data.append(
            {
                "name": name,
                "size_kb": path.stat().st_size / 1024,
                "timestamp": path.stat().st_mtime,
                "action": action["action"] if action else "Unknown",
                "action_time": action["timestamp"] if action else None,
            }
        )

    return jsonify(screenshot_data)


@app.route("/api/screenshot/<filename>")
def get_screenshot(filename):
    """API: Serve screenshot file"""
    return send_from_directory(SCREENSHOTS_DIR, filename)


@app.route("/api/delete/<filename>", methods=["POST"])
def delete_screenshot(filename):
    """API: Delete a screenshot"""
    screenshot_path = SCREENSHOTS_DIR / filename

    if not screenshot_path.exists():
        return jsonify({"error": "File not found"}), 404

    try:
        screenshot_path.unlink()
        return jsonify({"success": True, "message": f"Deleted {filename}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/stats")
def get_stats():
    """API: Get current statistics"""
    screenshots = get_screenshot_list()
    total_size = sum((SCREENSHOTS_DIR / s).stat().st_size for s in screenshots)

    # Get AI activity stats
    ai_activities = []
    if DB_PATH.exists():
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT content, content_type, created_at
                FROM observations
                WHERE content_type IN ('ai_activity', 'ai_clipboard', 'ai_conversation')
                ORDER BY created_at DESC
                LIMIT 50
            """
            )
            ai_activities = [
                {"content": row[0], "type": row[1], "time": row[2]} for row in cursor.fetchall()
            ]
            conn.close()
        except Exception:
            pass

    return jsonify(
        {
            "count": len(screenshots),
            "size_mb": total_size / (1024 * 1024),
            "db_exists": DB_PATH.exists(),
            "db_size_mb": DB_PATH.stat().st_size / (1024 * 1024) if DB_PATH.exists() else 0,
            "ai_activities": ai_activities,
        }
    )


@app.route("/api/ai-activity")
def get_ai_activity():
    """API: Get all AI activity logs"""
    if not DB_PATH.exists():
        return jsonify([])

    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT content, content_type, created_at
            FROM observations
            WHERE content_type IN ('ai_activity', 'ai_clipboard', 'ai_conversation')
            ORDER BY created_at DESC
        """
        )
        activities = [
            {"content": row[0], "type": row[1], "time": row[2]} for row in cursor.fetchall()
        ]
        conn.close()
        return jsonify(activities)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Create templates directory and HTML
TEMPLATE_DIR = Path(__file__).parent / "templates"
TEMPLATE_DIR.mkdir(exist_ok=True)

TEMPLATE_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>Recording Review</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .stats { display: flex; gap: 20px; margin: 15px 0; }
        .stat { flex: 1; background: #e3f2fd; padding: 15px; border-radius: 4px; text-align: center; }
        .viewer { background: white; padding: 20px; border-radius: 8px; }
        .screenshot-container { text-align: center; margin: 20px 0; position: relative; }
        .screenshot { max-width: 100%; max-height: 600px; border: 2px solid #ddd; border-radius: 4px; }
        .controls { display: flex; justify-content: center; gap: 10px; margin: 20px 0; }
        .btn { padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
        .btn-primary { background: #4CAF50; color: white; }
        .btn-primary:hover { background: #45a049; }
        .btn-danger { background: #f44336; color: white; }
        .btn-danger:hover { background: #da190b; }
        .btn-secondary { background: #008CBA; color: white; }
        .btn-secondary:hover { background: #007399; }
        .btn:disabled { background: #ccc; cursor: not-allowed; }
        .info { background: #f9f9f9; padding: 15px; border-radius: 4px; margin: 10px 0; }
        .info-label { font-weight: bold; color: #666; }
        .action-text { font-family: monospace; background: #f4f4f4; padding: 8px; border-radius: 4px; }
        .counter { font-size: 18px; font-weight: bold; margin: 10px 0; }
        .deleted-notice { background: #ffebee; color: #c62828; padding: 10px; border-radius: 4px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Recording Review</h1>
            <div class="stats">
                <div class="stat">
                    <div style="font-size: 24px; font-weight: bold;" id="total-count">{{ total_screenshots }}</div>
                    <div>Total Screenshots</div>
                </div>
                <div class="stat">
                    <div style="font-size: 24px; font-weight: bold;" id="total-size">{{ total_size_mb }} MB</div>
                    <div>Total Size</div>
                </div>
                <div class="stat">
                    <div style="font-size: 24px; font-weight: bold;" id="current-index">0</div>
                    <div>Current Index</div>
                </div>
            </div>
            <p><em>Review your screenshots and delete any sensitive data before submitting to GCS</em></p>
        </div>

        <div class="viewer">
            <div class="counter" id="counter"></div>

            <div class="screenshot-container">
                <img id="screenshot" class="screenshot" src="" alt="Screenshot">
            </div>

            <div class="info">
                <div class="info-label">Action:</div>
                <div class="action-text" id="action-text">Loading...</div>
            </div>

            <div class="info">
                <div class="info-label">Filename:</div>
                <div id="filename">-</div>
            </div>

            <div class="info">
                <div class="info-label">Size:</div>
                <div id="filesize">-</div>
            </div>

            <div id="deleted-notice" class="deleted-notice" style="display: none;">
                [OK] Screenshot deleted
            </div>

            <div class="controls">
                <button class="btn btn-secondary" id="prev-btn" onclick="navigate(-1)"><- Previous</button>
                <button class="btn btn-danger" id="delete-btn" onclick="deleteScreenshot()">Delete</button>
                <button class="btn btn-secondary" id="next-btn" onclick="navigate(1)">Next -></button>
            </div>

            <div class="controls">
                <button class="btn btn-primary" onclick="finishReview()">[OK] Finish Review</button>
            </div>
        </div>
    </div>

    <script>
        let screenshots = [];
        let currentIndex = 0;

        async function loadScreenshots() {
            const response = await fetch('/api/screenshots');
            screenshots = await response.json();
            if (screenshots.length > 0) {
                showScreenshot(0);
            } else {
                document.getElementById('counter').textContent = 'No screenshots found';
            }
        }

        function showScreenshot(index) {
            if (screenshots.length === 0) return;

            currentIndex = Math.max(0, Math.min(index, screenshots.length - 1));
            const screenshot = screenshots[currentIndex];

            document.getElementById('screenshot').src = `/api/screenshot/${screenshot.name}`;
            document.getElementById('counter').textContent = `Screenshot ${currentIndex + 1} of ${screenshots.length}`;
            document.getElementById('current-index').textContent = currentIndex + 1;
            document.getElementById('action-text').textContent = screenshot.action;
            document.getElementById('filename').textContent = screenshot.name;
            document.getElementById('filesize').textContent = `${screenshot.size_kb.toFixed(1)} KB`;

            // Update button states
            document.getElementById('prev-btn').disabled = currentIndex === 0;
            document.getElementById('next-btn').disabled = currentIndex === screenshots.length - 1;

            // Hide deleted notice
            document.getElementById('deleted-notice').style.display = 'none';
        }

        function navigate(direction) {
            showScreenshot(currentIndex + direction);
        }

        async function deleteScreenshot() {
            if (screenshots.length === 0) return;

            const screenshot = screenshots[currentIndex];

            if (!confirm(`Delete ${screenshot.name}?`)) {
                return;
            }

            try {
                const response = await fetch(`/api/delete/${screenshot.name}`, {
                    method: 'POST'
                });

                if (response.ok) {
                    // Show deleted notice
                    document.getElementById('deleted-notice').style.display = 'block';

                    // Remove from list
                    screenshots.splice(currentIndex, 1);

                    // Update stats
                    await updateStats();

                    // Show next screenshot or previous if at end
                    if (screenshots.length === 0) {
                        document.getElementById('counter').textContent = 'No screenshots remaining';
                        document.getElementById('screenshot').src = '';
                        document.getElementById('action-text').textContent = 'All screenshots deleted';
                    } else if (currentIndex >= screenshots.length) {
                        showScreenshot(screenshots.length - 1);
                    } else {
                        showScreenshot(currentIndex);
                    }
                } else {
                    alert('Failed to delete screenshot');
                }
            } catch (error) {
                alert('Error: ' + error);
            }
        }

        async function updateStats() {
            const response = await fetch('/api/stats');
            const stats = await response.json();
            document.getElementById('total-count').textContent = stats.count;
            document.getElementById('total-size').textContent = `${stats.size_mb.toFixed(1)} MB`;
        }

        function finishReview() {
            const remaining = screenshots.length;
            const message = `Review complete!\\n\\nRemaining screenshots: ${remaining}\\n\\n` +
                `Next step: Run 'python submit.py -s init --snake_name YOUR_NAME' to submit`;
            alert(message);
            window.close();
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft') navigate(-1);
            if (e.key === 'ArrowRight') navigate(1);
            if (e.key === 'Delete' || e.key === 'Backspace') {
                e.preventDefault();
                deleteScreenshot();
            }
        });

        // Load on start
        loadScreenshots();
    </script>
</body>
</html>
"""

# Write template
with open(TEMPLATE_DIR / "review.html", "w") as f:
    f.write(TEMPLATE_HTML)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Review recording before submission")
    parser.add_argument(
        "--data-dir", default="data", help="Directory containing recordings (default: data)"
    )
    parser.add_argument(
        "--port", type=int, default=5555, help="Port for web server (default: 5555)"
    )

    args = parser.parse_args()

    # Update global paths
    global DATA_DIR, SCREENSHOTS_DIR, DB_PATH
    DATA_DIR = Path(args.data_dir).expanduser()
    SCREENSHOTS_DIR = DATA_DIR / "screenshots"
    DB_PATH = DATA_DIR / "actions.db"

    # Validate
    if not SCREENSHOTS_DIR.exists():
        print(f"ERROR: Screenshots directory not found: {SCREENSHOTS_DIR}")
        print(
            "Have you run 'gum' to record data? If your data is in a different location, "
            "add a --data-dir flag to specify the data directory."
        )
        return 1

    screenshots = get_screenshot_list()
    if not screenshots:
        print(f"WARNING: No screenshots found in {SCREENSHOTS_DIR}")
        return 1

    print(f"\n{'='*70}")
    print("Recording Review Server")
    print(f"{'='*70}")
    print(f"Screenshots: {len(screenshots)}")
    print(f"Data dir:    {DATA_DIR}")
    print(f"\nStarting web server on http://localhost:{args.port}")
    print("\nInstructions:")
    print("  - Use <- -> arrow keys or buttons to navigate")
    print("  - Press Delete/Backspace or click Delete button to remove")
    print("  - Review all screenshots for privacy/sensitivity")
    print("  - Close browser when done")
    print(f"\n{'='*70}\n")

    app.run(host="localhost", port=args.port, debug=False)


if __name__ == "__main__":
    main()
