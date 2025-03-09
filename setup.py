from setuptools import setup

setup(
    name="backend",
    version="0.1.0",
    packages=["backend", "backend.api", "backend.models", "backend.routes", "backend.services", "backend.migration"],
    author="Your Name",
    author_email="your.email@example.com",
    description="Backend services for a trading bot application",
    keywords="trading, finance, stocks, alpaca",
)
