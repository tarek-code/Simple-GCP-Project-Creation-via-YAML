# GCP Project Creator GUI

A user-friendly web interface for creating and deploying Google Cloud Platform projects using YAML configurations.

## Features

- 🏗️ **Project Builder**: Step-by-step project configuration
- 📋 **Configuration Manager**: Edit and manage existing configurations
- 🚀 **Deploy & Monitor**: Deploy configurations with real-time progress
- 📚 **Help & Examples**: Built-in documentation and examples

## Installation

1. Install dependencies:
```bash
cd gui
pip install -r requirements.txt
```

2. Run the application:
```bash
streamlit run streamlit_app.py
```

3. Open your browser to `http://localhost:8501`

## Usage

### 1. Project Builder
- Configure project settings (ID, billing account, labels)
- Select required APIs
- Add infrastructure resources (VPC, VMs, storage, etc.)
- Generate YAML configuration

### 2. Configuration Manager
- View existing configurations
- Edit YAML files directly
- Delete unwanted configurations

### 3. Deploy & Monitor
- Select configuration to deploy
- Choose deployment options (plan-only, auto-approve)
- Monitor deployment progress
- View deployment results

### 4. Help & Examples
- Quick start guide
- Example configurations
- Troubleshooting tips

## Integration

The GUI integrates seamlessly with the existing `scripts/deploy.py` script:

- Generates YAML configurations in the `configs/` directory
- Calls the deploy script with proper parameters
- Displays deployment progress and results
- Handles errors and timeouts gracefully

## Requirements

- Python 3.7+
- Streamlit
- PyYAML
- Access to the project's `scripts/deploy.py` and `modules/` directory

## Architecture

```
gui/
├── streamlit_app.py      # Main GUI application
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

The GUI is built with Streamlit and provides a modern, responsive interface for managing GCP project configurations.
