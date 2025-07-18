# Misaligned Boards Detection Application

A PySide6-based application for detecting misaligned boards using computer vision and OpenCV.

## Features

- Real-time video processing from cameras or video files
- Interactive ROI (Region of Interest) selection with visual feedback
- Line detection and angle analysis for board alignment
- Defect logging and database storage
- Camera settings management (exposure, gain, FPS, resolution)
- Template-based pallet detection configuration
- Socket communication for sensor integration
- Modern PySide6 user interface

## Project Structure

```
├── main.py                 # Main application entry point
├── requirements.txt        # Python dependencies
├── README.md              # Project documentation
└── src/
    ├── core/              # Core processing components
    │   ├── __init__.py
    │   ├── video_thread.py    # Video processing thread
    │   └── detection_engine.py # Line detection and analysis
    ├── ui/                # User interface components
    │   ├── __init__.py
    │   ├── video_widget.py    # Video display widget
    │   └── dialogs.py         # Settings and setup dialogs
    ├── utils/             # Utility components
    │   ├── __init__.py
    │   ├── database_manager.py # SQLite database operations
    │   ├── camera_manager.py   # Camera detection and selection
    │   └── template_manager.py # Template file operations
    └── config/            # Configuration files
        └── __init__.py
```

## Installation

1. Install Python 3.8 or higher
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the application:
```bash
python main.py
```

### Key Features

- **Video Input**: Select camera or video file from File menu
- **ROI Selection**: Click "Select ROI" and drag to define detection area
- **Settings**: Configure camera and detection parameters via Settings menu
- **Defect Viewing**: View detected defects via View menu
- **Templates**: Save and load pallet detection configurations

## Dependencies

- OpenCV 4.8+ for computer vision operations
- NumPy for numerical computations
- PySide6 for the user interface
- SQLite for defect logging

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 