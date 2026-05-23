# setup.py
"""
Setup script for E-Commerce Sales Analytics Project
Author: ANGEL-MAVUYANGWA
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    name="ecommerce-sales-analytics",
    version="1.0.0",
    author="Angel",
    author_email="your.email@example.com",
    description="Comprehensive E-Commerce Sales Analytics Project",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ANGEL-MAVUYANGWA/E-Commerce-Sales-Analytics-.git",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "run-data-cleaning=scripts.data_cleaning:main",
            "run-analysis=scripts.data_analysis:main",
            "run-visualization=scripts.visualization:main",
            "run-dashboard=dashboard.app:main",
        ],
    },
)