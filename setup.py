import textwrap

from setuptools import setup, find_packages

from src.utils.settings import read_version

version = read_version()

setup(
    name="surfgate.app",  # Required
    version=version,  # Required
    description=textwrap.dedent(
        """
The surfgate.app API offers endpoints that you can connect to using your web-service user license key. 
These endpoints allow you to perform actions such as evaluating potential content violation rates and 
retrieving already evaluated rates.
         """
    ),
    url="https://surfgate.app",
    author="Dmitry Sagoyan",
    author_email="contact@surfgate.app",
    keywords=["surfgate"],
    setup_requires=["setuptools==69.1.1", "wheel~=0.42.0", "PyYAML~=6.0.1"],
    python_requires=">=3.11, <4",
    install_requires=[
        "beautifulsoup4~=4.12.3",
        "bs4",
        "datedelta",
        "fake-useragent~=1.5.1",
        "fastapi",
        "joblib",
        "keras",
        "nltk",
        "numpy",
        "pandas",
        "psycopg2-binary",
        "pydantic[email]",
        "requests==2.31.0",
        "scikit-learn",
        "scipy",
        "selenium",
        "sqlalchemy[mypy]",
        "tqdm",
        "uvicorn[standard]",
    ],
    extras_require={
        "dev": ["isort", "black", "autoflake"],
        "test": ["pylama", "pytest", "mock"],
        "gpu": ["tensorflow-gpu"],
    },
    packages=find_packages(),
    package_dir={"surfgateapp": "src"},
    package_data={
        "src": [
            "data/*.txt",
            "backup/*.bak",
            "keys/production/*.pem",
            "logs/*.log",
            "settings/production.yaml",
            "settings/development.yaml",
            "trained_data/*.pkl",
        ]
    },
    entry_points={  # Optional
        "console_scripts": [
            "surfgateapp_init=src.init:main",
            "surfgateapp_train=src.train:main",
            "surfgateapp_app=src.app:main",
        ]
    },
    project_urls={"Promotion Site": "https://surfgate.app"},
)
