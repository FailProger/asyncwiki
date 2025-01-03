from setuptools import setup, find_packages


__version__ = "0.1.2"

with open("README.md", "r", encoding="UTF-8") as file:
    long_description = file.read()

requires_list = [
    "aiohttp==3.11.11",
    "beautifulsoup4==4.12.3",
    "lxml==5.3.0",
    "SQLAlchemy==2.0.36",
    "pyspellchecker==0.8.2"
]

setup(
    name="asyncwiki",
    version=__version__,
    author="Vyacheslav Pervakov",
    author_email="WsrrcalzWehgwmD@protonmail.com",
    description="Asynchronous work with Wikipedia for asyncio and Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/FailProger/asyncwiki.git",
    project_urls={
        "GitHub": "https://github.com/FailProger/asyncwiki.git",
        "PyPI": "https://pypi.org/project/asyncwiki/"
    },
    license="MIT License",
    license_file="LICENSE",
    keywords=["Python", "asynchronous", "asyncio", "aiohttp", "Wikipedia"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License"
    ],
    packages=find_packages(),
    python_requires = ">=3.13",
    install_requires=requires_list
)
