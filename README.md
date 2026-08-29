# Spycer - GUI for 5 axes 3D printer

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/epit3d/spycer)

## Table of Contents

- [About](#about)
- [Ask for demo](#ask-for-demo)
- [Basic usage](#basic-usage)
- [Installation](#installation)
- [Contributing](#contributing)

## About

Spycer is a GUI tool for innovative 5 axes 3D printer. See our [website](https://epit3d.com/).

## Ask for demo

If you want to try our Five Axes Slicing Program and interested in 5 axes 3D printer - feel free to contact us: [Info@epit3d.ru](mailto:Info@epit3d.ru?subject=FASP%20demo%20request&body=Hello%2C%20I%20want%20to%20try%20Spycer%20and%20FASP%20slicer)

### Features of FASP slicer (Five Axes Slicing Program):

- [x] Interactive calibration
<details>
    <summary>[x] 3D slicing</summary>
    <img src="imgs/simple.gif"/>
</details>
<details>
    <summary>[x] Multi-plane slicing</summary>
    <img src="imgs/multiplane.gif"/>
</details>
<details>
    <summary>[x] Cone slicing</summary>
    <img src="imgs/conical.gif"/>
</details>
<details>
    <summary>[x] Cylinder slicing</summary>
    <img src="imgs/cylindrical.gif"/>
</details>

- [] Smooth slicing
- [x] Lids processing
- [x] Supports processing
- [x] Gcode preview (with rotations of bed)

## Basic usage

Right now you can use Spycer in "preview" mode.
It means that you can locally setup Spycer and see our possibilities without having slicer and 5 axes 3D printer.
Slicer software we develop is not open source yet, but you can ask us for demo.

For legacy use you can try latest open source version of slicer: [goosli](https://github.com/epit3d/goosli).
We do not have capabilities to support integration with current Spycer version, but you may try old Spycer version from about Oct 24, 2020.

## Installation

### Prerequisites

Python 3.10 is required. We recommend using [uv](https://docs.astral.sh/uv/) for Python version management:

```bash
# Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Python 3.10 via uv
uv python install 3.10
```

### Setup

1. Create virtual environment: `uv venv --python 3.10`
2. Activate virtual environment:
   - Windows: `venv\Scripts\activate.bat`
   - Linux/macOS: `source .venv/bin/activate`
3. Install dependencies:
   - Windows: `uv pip install -r win-req.txt`
   - Linux: `uv pip install -r linux-req.txt`
   - macOS: `uv pip install -r macos-req.txt`
4. Run Spycer: `python main.py`

## Contributing

Feel free to open issues and create pull requests. We will be happy to see your contributions and ideas.
