# benchcompress

A benchmarking framework for evaluating compression algorithms on scientific data arrays.

Latest benchmark results: https://magland.github.io/benchcompress/

Paper (WIP): https://magland.github.io/benchcompress/paper

## Overview

Benchcompress is a comprehensive benchmarking framework for evaluating compression algorithms on scientific data arrays. The system follows an automated workflow:

1. **Defining Components**
   - Algorithms are implemented in `benchcompress/src/benchcompress/algorithms/`
   - Datasets are defined in `benchcompress/src/benchcompress/datasets/`
   - Each component specifies metadata like version, tags, and compatibility requirements

2. **Automated Benchmarking**
   - Benchmarks run automatically via GitHub Actions on pushes to main branch
   - For each compatible algorithm-dataset pair, measures:
     - Compression ratio
     - Encoding throughput (MB/s)
     - Decoding throughput (MB/s)
   - Results are verified by decompressing and comparing with original data

3. **Result Storage**
   - Results are committed to a dedicated `benchmark-results` branch
   - Local and remote caching system prevents redundant rerunning of benchmarks (only modified or added components are re-benchmarked)
   - Caching is based on algorithm and dataset versions

4. **Web Interface**
   - Interactive visualization at https://magland.github.io/benchcompress/
   - Filter and sort results by dataset or algorithm
   - Visual charts for comparing performance metrics
   - Export results to CSV for further analysis

## For developers

The project consists of two main components:

- `benchcompress/`: Python package containing the core benchmarking framework, algorithms, and datasets
- `web-ui/`: React-based web interface for visualizing benchmark results

### Local Development Setup

1. Install Python dependencies:
```bash
cd benchcompress
pip install -e .

benchcompress --help
benchcompress list
benchcompress run --help
```

2. Install web UI dependencies:
```bash
cd web-ui
npm install
```

3. Run web UI locally:
```bash
cd web-ui
npm run dev
```

### Code Formatting

This project uses pre-commit hooks to automatically check format code before each commit. The formatting includes:
- Python code formatting using black
- TypeScript/JavaScript code formatting using npm scripts
- C++ code formatting using clang-format

To set up the pre-commit hooks after cloning the repository:

1. Install pre-commit:
```bash
pip install pre-commit
```

2. Install the git hook scripts:
```bash
pre-commit install
```

After this setup, code will be automatically checked for formatting when you make a commit.

Running `./devel/format_code.sh` which will format all code in the repository.
