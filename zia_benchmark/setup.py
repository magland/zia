from setuptools import setup, find_packages

setup(
    name="zia_benchmark",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "numpy",
        "scipy",
        "zstandard",
        "simple_ans",
        "requests",
        "lindi",
        "brotli",
        "click",
        "numba"
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "zia-benchmark=zia_benchmark.cli:main",
        ],
    },
    author="Jeremy Magland",
    description="Benchmarking compression methods for numeric arrays",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    keywords="compression, signal processing",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11"
    ],
)
