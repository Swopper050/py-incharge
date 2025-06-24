from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="vattenfall-charger",
    version="0.1.0",
    author="Bram",
    author_email="bram@example.com",
    description="A Python package for remotely controlling Vattenfall EV charging stations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bram/vattenfall-charger",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Hardware :: Hardware Drivers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "ruff",
            "black",
            "pytest",
            "pytest-asyncio",
            "twine",
            "build",
        ],
    },
    entry_points={
        "console_scripts": [
            "vattenfall-charger=vattenfall_charger.charger:main",
        ],
    },
    keywords="vattenfall ev charger electric vehicle remote control websocket",
    project_urls={
        "Bug Reports": "https://github.com/bram/vattenfall-charger/issues",
        "Source": "https://github.com/bram/vattenfall-charger",
        "Documentation": "https://github.com/bram/vattenfall-charger#readme",
    },
)