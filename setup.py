from setuptools import find_packages, setup

setup(
    name="agent-builder",
    version="0.1.0",
    description="Reusable framework for autonomous multi-agent organizations",
    author="Agent Builder Contributors",
    packages=find_packages(include=["agent_builder", "agent_builder.*", "cli", "cli.*"]),
    include_package_data=True,
    install_requires=[
        "pyyaml>=6.0",
        "pydantic>=2.0",
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "llm": [
            "google-generativeai>=0.3.0",
            "anthropic>=0.7.0",
            "openai>=1.0.0",
        ],
        "dev": ["pytest>=7.4.0"],
    },
    entry_points={"console_scripts": ["agent-builder=cli.main:main"]},
    python_requires=">=3.10",
)
