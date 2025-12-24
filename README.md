# Stanford Study on Human-AI Collaboration
Thank you for agreeing to participate our Stanford study on Human-AI collaboration! This is the starter repo for the participants intended to help you design and test Python snake bots.

## Quick-Start Checklist

Use this checklist to verify your setup is complete before starting:

- [ ] **Prerequisites installed**: conda, Docker, git
- [ ] **Repo cloned with submodules**: `git clone --recurse-submodules ...`
- [ ] **Conda environment created**: `conda activate snake` works
- [ ] **Docker daemon running**: `docker info` shows server info (not error)
  - macOS/Windows: Docker Desktop must be **open and running**
  - Linux: `sudo systemctl start docker`
- [ ] **Battlesnake CLI built**: `./rules/battlesnake --help` works
- [ ] **Config file set up**: `eval/snapshot_config.json` exists with your credentials
- [ ] **Recording tool installed**: `gum --help` works

## Purpose of the Study
This study intends to understand the determinants of human-AI collaboration through observing how developers work with AI to develop snake bots in Python. We use game engine from [BattleSnake](https://play.battlesnake.com/), an online arena that hosts matches between snake bots and assigns ratings to developers based on their snake bots. The [rules of BattleSnake](https://docs.battlesnake.com/rules) are pretty straightforward if you have ever played [slither.io](slither.io) before. We will evenly split participants into two groups, one group with and one group without AI tools, to work on building snake bots, and we will assess performance of snake bots and give you chances to make continuous improvement. Eventually, we will run duel tournaments between the snakes and award the final winner.

## Procedure of the Study
### Setup
Participants should familiarize themselves with the rules of the game and [set up the game environment](instructions-on-setting-up-the-game-dev-environment). Once the game is set up, participants can install the [screen recording tool](instructions-on-setting-up-the-screen-recording-tool). **Please do not start your screen recording until everything is set up and tested!**

### Experimental Stages:
1. The participants should first work on developing a snake bot in Python, with as much time as up to 2 hours, **without the help of any AI tools**. Participants can make iterations on their snakes by benchmarking their snakes against the [example snake bots](example-snakes) we provide to you and have some senses of how well they perform and what strategies are implemented.
2. During the 2 hours window, the participants **should open their recording tool throughout**. In order to prevent privacy leakages, participants should **only select the working windows** (e.g. VSCode, Safari, Chrome, Terminal, etc) and avoid including windows that expose personal information. **Please make sure that you select at least one Chrome window to record, because you are mostly likely needing to read some web information and view your game records.** After the 2 hour window ends, the participants will submit their snake bots to our cloud storage via 
```python submit.py -s init --snake_name YOUR_SNAKE_NAME```
3. The snakes will then be collected and benchmarked across opponents. We will return you with the ratings of the snakes as well as highlights of your snakes against other players.
4. Second stage: In a maximum of 2 hours, you can work on improving your snakes based on the battle trajectories. During the 2 hours, please also make sure that the screen recording tool is on and submit your snakes to our cloud storage via 
```python submit.py -s final --snake_name YOUR_SNAKE_NAME```. Please keep your snake names consistent!
**Participants from the AI group can use AI tools while the control group cannot.**
5. We will return your final ratings after the snakes are all collected. Please also make sure to complete the post-study survey (link will be provided via email).

## Instructions on Setting Up the Game Dev Environment

### Quick Setup (Recommended)
After cloning the repo or the repo you created based on this template, you can run our automated setup script:
```bash
git clone --recurse-submodules https://github.com/abehou/haic_starter.git
cd haic_starter
./setup.sh
```

This script will automatically:
- Create the conda environment
- Install all dependencies
- Build the BattleSnake CLI
- Set up the recording tool
- Configure the tournament script

If you prefer manual setup or encounter issues, follow the detailed steps below.

### Manual Setup (Step by Step)
0. First, clone this repo or create a new repo based on this github template (recommended):

If you clone:
```bash
git clone --recurse-submodules https://github.com/abehou/haic_starter.git
git submodule update --init --recursive # In case you forgot to clone with the recursive flag.
``` 
Or you can clone after use this template to create your own repo.

1. Set up a conda environment called 'snake' (must use this name in order for run_local_tournament.sh to work):
```bash
conda create -n snake python=3.10
conda activate snake
pip install -r requirements.txt 
```
2. Install [Docker](https://docs.docker.com/desktop/) and ensure the Docker daemon is running:

**macOS / Windows:**
```bash
# Install Docker Desktop from https://docs.docker.com/desktop/
# IMPORTANT: Open Docker Desktop and keep it running!
# The Docker daemon only runs when Docker Desktop is open.
docker --help  # Verify installation
```

**Linux:**
```bash
# Option A: Install Docker Engine (recommended - no GUI needed)
# Follow: https://docs.docker.com/engine/install/
# The daemon runs as a system service automatically

# Option B: Install Docker Desktop (GUI-based, similar to Mac/Windows)
# The daemon only runs when Docker Desktop is open

# Start/verify Docker daemon:
sudo systemctl start docker    # Start the daemon
sudo systemctl enable docker   # Auto-start on boot
docker --help                  # Verify installation
```
3. Install Go and install rules-cli: 
```bash
conda activate snake
conda install conda-forge::go
cd rules && go build -o battlesnake ./cli/battlesnake/main.go && cd ..
```
To test: `./rules/battlesnake --help`

4. Configure `run_dev_tournament.sh`: 
- **If you are running on your local machine**, do:
```bash
cp run_dev_tournament_local.sh run_dev_tournament.sh
chmod +x run_dev_tournament.sh
```
- **If you are running a remote cluster**, you need to:
```bash
cp run_dev_tournament_remote.sh.template run_dev_tournament.sh
chmod +x run_dev_tournament.sh
``` 
and modify the slurm headers in `run_dev_tournament_remote.sh` according to your cluster configs.

5. Configure `eval/snapshot_config.json.template`:
We will email you your personal `snapshot_config.json`. Make sure to paste it in under the `eval` directory and change the file name to `snapshot_config.json`. Alternatively, copy our template and paste over the content of your json config obtained from us:
```bash
cp eval/snapshot_config.json.template eval/snapshot_config.json
```
and then copy & paste the content of json config from us.

> ⚠️ **IMPORTANT: Your config URLs expire in 7 days from when they were generated.** Please complete both stages of the study (init and final submissions) within this timeframe. If your URLs expire before you finish, contact the study coordinators to request new credentials.

## Instructions on Setting Up the Screen Recording tool

### Windows

```bash
conda activate snake
cd record
pip install -e .[windows] && cd ..
```

This installs Windows-specific dependencies required for window detection:
- `pywin32` - Required for detecting active windows via Windows API
- `psutil` - Required for process information
- `uiautomation` - Optional, for enhanced browser tab detection

### macOS

```bash
conda activate snake
cd record
pip install -e . && cd ..
```

Make sure to enable recording permissions: go to System Preferences -> Privacy & Security -> Accessibility, and allow recording for the app you use to edit code (e.g., VSCode or Terminal).

### Linux

Before installing, you need to install build tools, GUI libraries, GObject dependencies, window management tools, and screenshot utilities:
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

Then install the recording tool:
```bash
conda activate snake
cd record
# Option 1: Install with Linux extras (includes PyGObject, python-xlib, ewmh)
pip install -e .[linux] && cd ..

# Option 2: If PyGObject installation fails, install without Linux extras
# pip install -e . && cd ..
```

### Using the Recorder

**When to Start Recording:**
- Start `gum` **after** all setup is complete and tested
- Start recording **before** you begin developing your snake
- Keep recording running throughout your entire development session

**How to Record:**
```bash
conda activate snake
gum
```

**Window Selection:**
- `gum` will prompt you to select which windows to record
- Select ONLY windows relevant to the study: VSCode/IDE, Terminal, browser window for documentation
- **Do NOT include** personal browser windows, email, messaging apps, etc.
- The tool only captures activity in selected windows

**During Recording:**
- Recording auto-stops after 45 minutes of inactivity in selected windows
- If taking a break, you can stop recording with `Ctrl+C` and restart later
- Each recording session is saved separately

**Stopping Recording:**
- Press `Ctrl+C` in the terminal where `gum` is running
- Review your recordings before submitting: `python review_recording.py`

> 💡 **Tip:** If you need to take a break longer than 45 minutes, stop the recording with `Ctrl+C` and start a new session when you return.

**If you were able to do them, great job and give yourself a round of applause! Now we are all set up and ready to develop some snake bots! Don't forget to start gum for the recording!**

### Example Snakes
We have provided a minimal starter Python snake bot under `your_snake/`. Please keep developing your snake under this directory and make sure that the there's always a `main.py` that once ran can start your snake server.

To help you develop the snakes, we have prepared some example snakes in `example_snakes/`. Feel free to read their codes and get a sense of how their snakes get built. 

### Minimally Test Your Snake
First, make sure you have built the battlesnake-cli by 
```bash
conda activate snake
conda install conda-forge::go
cd rules && go build -o battlesnake ./cli/battlesnake/main.go && cd ..
```
Then, run:
`PORT=7123 python your_snake/main.py`
Open a new terminal window, and then:
`./rules/battlesnake play -W 11 -H 11 --name your_snake --url http://localhost:7123 -g solo -v`

### Benchmark Your Snake
We have provided `run_dev_tournament.sh` to run a mini-tournament between your snake and all the example snake bots to help you understand your snake's performance. The tournament results will be stored at `tournaments/round_robin_*` with the timestamp that occurs. You can click into the games under the tournaments records and view `tournaments/round_robin_*/trueskill_results.json` to see the ranking of snake bots. 

**High-level overview of `run_dev_tournament.sh`**: Basically, this script generates `docker-compose.test.yml`, which orchestrates a bunch of docker images from `example_snakes` and builds servers for each snake. Then, we run `rules/battlesnake` to host the games, request to the snake servers to observe their movements, and repeat for every snake duel pairs. Lastly, we aggregate the results and upload a snapshot of your snake every time you run this script.

**Why do you need to edit `eval/snapshot_config.json`?**: We need to record your snake code and performance every time you `run_dev_tournament.sh` to have a better understanding of the workflow and trajectory. Only code files under **your_snake** will be automatically uploaded and we won't upload any additional information. Once we have the snapshots, we will analyze the code changes between tournaments.

### Visualize Your Tournament
run:
`conda activate snake` and then `python -m game_viewer.server`. Click on `http://127.0.0.1:5000` and you should be able to view all the game trajectories on your browser. You can try to figure out based on how to improve your snake based on the actual performance and strategies it displays.

### Resources for Improving Your Snakes
1. [BattleSnake Starter in Python](https://github.com/BattlesnakeOfficial/starter-snake-python)
2. [A list of BattleSnake resources](https://github.com/BattlesnakeOfficial/awesome-battlesnake)

### Reviewing Your Recordings
When you finish your recording, you can run `python review_recording.py`, which will lead you to a web-based UI where you can view your recording screenshots. You can choose to delete any screenshots that contain sensitive information.

**Note:** Your recordings are automatically uploaded along with your snake code when you run `python submit.py -s init` or `python submit.py -s final`. If you want to submit only recordings without snake code, you can run:
```bash
python submit.py --recordings-only
```

Your recordings will be anonymized and deleted after the study.

## Troubleshooting

### Common Issues

#### Setup Script Fails
If `./setup.sh` fails, try running the manual setup steps one by one. The most common issues are:
- **Conda not initialized**: Make sure to run `conda init` first, then restart your terminal
- **Docker not running**: On macOS, make sure Docker Desktop is open and running

#### "conda: command not found"
Make sure conda is properly installed and initialized:
```bash
# Add conda to your shell (replace with your conda installation path)
source ~/miniconda3/etc/profile.d/conda.sh
conda init
```
Then restart your terminal.

#### Go Build Fails
If building battlesnake fails:
```bash
conda activate snake
conda install -c conda-forge go -y
cd rules
go build -o battlesnake ./cli/battlesnake/main.go
```

#### Recording Tool Issues

**macOS - "Screen recording permission denied":**
1. Go to System Preferences → Privacy & Security → Screen Recording
2. Add Terminal (or your IDE) to the allowed apps
3. Restart Terminal/IDE

**Linux - Window selection not working:**
Make sure you have the required packages:
```bash
# Arch
sudo pacman -S wmctrl maim

# Ubuntu/Debian
sudo apt install wmctrl maim xdotool

# Fedora
sudo dnf install wmctrl maim xdotool
```

**Linux - Screenshots failing:**
If you see "maim capture failed" or similar:
- Make sure you're running X11 (not Wayland): `echo $XDG_SESSION_TYPE`
- If on Wayland, the recording tool has limited support. Consider switching to X11.

#### Tournament Script Issues

**"Docker daemon not running":**
- **macOS/Windows:** Open Docker Desktop application and keep it running. The daemon only runs when the app is open (can be minimized to system tray).
- **Linux (Docker Engine):** Run `sudo systemctl start docker`. To auto-start on boot: `sudo systemctl enable docker`
- **Linux (Docker Desktop):** Open Docker Desktop and keep it running, same as macOS/Windows.

To verify Docker is running: `docker info` (should show server info, not an error)

**"Port already in use":**
Kill existing processes:
```bash
docker-compose -f docker-compose.test.yml down
# Or manually kill processes on ports 8000-8010
```

#### Submission Issues

**"Config not found":**
Make sure you've set up your personal config:
```bash
cp eval/snapshot_config.json.template eval/snapshot_config.json
# Then edit the file with your credentials from the email
```

### Getting Help
If you encounter issues not covered here, please contact the study coordinators via email.
