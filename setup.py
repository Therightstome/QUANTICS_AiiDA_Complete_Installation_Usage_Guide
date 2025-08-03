#!/usr/bin/env python3
"""
Setup script for QUANTICS Professional GUI
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="quantics-professional-gui",
    description="Professional interface for QUANTICS quantum dynamics calculations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Therightstome/QUANTICS_AiiDA_Complete_Installation_Usage_Guide",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "PyQt5>=5.15.0",
        "pathlib2>=2.3.0",
    ],
    extras_require={
        "aiida": [
            "aiida-core[atomic_tools]==2.6.2",
            "aiida-sge>=1.0.0", 
            "psycopg2-binary>=2.8.0",
            "paramiko>=2.7.0",
            "click-completion>=0.5.0",
        ],
        "dev": [
            "black>=22.0.0",
            "pytest>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "quantics-gui=quantics_gui:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["examples/**/*", "docs/**/*"],
    },
    keywords="quantics quantum dynamics mctdh vmcg aiida gui interface",
) 