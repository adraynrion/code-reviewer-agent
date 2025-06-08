import re
from pathlib import Path

from setuptools import setup, find_packages

def get_version():
    version_file = Path("code_reviewer_agent/__init__.py").read_text()
    version_match = re.search(r'^__version__ = ["\']([^"\']+)["\']', version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

# Read the contents of README.md
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [
        line.strip() for line in f if line.strip() and not line.startswith("#")
    ]

setup(
    name="code-reviewer-agent",
    version=get_version(),
    author="Adraynrion",
    author_email="adraynrion@citizenofai.com",
    description="An intelligent code review agent for GitHub and GitLab pull requests",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/adraynrion/code-reviewer-agent",
    packages=find_packages(
        include=["code_reviewer_agent", "code_reviewer_agent.*"]
    ),
    package_data={
        'code_reviewer_agent': ['py.typed'],
    },
    install_requires=requirements,
    extras_require={
        "dev": [
            "black>=24.0.0,<25.0.0",
            "flake8>=7.0.0,<8.0.0",
            "isort>=5.13.0,<6.0.0",
            "mypy>=1.8.0,<2.0.0",
            "pytest>=8.0.0,<9.0.0",
            "pytest-cov>=4.1.0,<5.0.0",
            "pytest-asyncio>=0.23.0,<0.24.0",
            "types-PyYAML>=6.0.0,<7.0.0",
            "types-requests>=2.31.0,<3.0.0",
            "types-setuptools>=69.5.0,<70.0.0",
            "types-pyinstaller>=6.13.0,<7.0.0",
            "flake8-annotations>=3.0.0,<4.0.0",
            "flake8-bandit>=4.1.0,<5.0.0",
            "flake8-bugbear>=24.0.0,<25.0.0",
            "flake8-comprehensions>=3.16.0,<4.0.0",
            "flake8-docstrings>=1.7.0,<2.0.0",
            "flake8-import-order>=0.18.0,<0.19.0",
            "flake8-print>=5.0.0,<6.0.0",
            "flake8-simplify>=0.21.0,<0.22.0",
            "pep8-naming>=0.14.0,<0.15.0",
            "autotyping>=24.9.0",
            "libcst>=1.1.0",
            "docformatter>=1.7.0,<2.0.0",
            "pycln>=2.4.0,<3.0.0"
        ],
    },
    entry_points={
        'console_scripts': [
            'code-reviewer=code_reviewer_agent.code_review_agent:main',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Version Control :: Git",
        "Typing :: Typed",
    ],
    python_requires=">=3.11.9,<3.12.0",
    keywords="git code review agent ai cli",
    project_urls={
        "Bug Reports": "https://github.com/adraynrion/code-reviewer-agent/issues",
        "Source": "https://github.com/adraynrion/code-reviewer-agent",
    },
    license="MIT",
)
