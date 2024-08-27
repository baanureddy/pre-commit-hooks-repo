from setuptools import setup, find_packages

setup(
    name="pre_commit_hooks",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        # List any dependencies your hook needs here
    ],
    entry_points={
        'console_scripts': [
            'pre-commit-hook-scan-from-server = pre_commit_hooks.scan:main',
        ],
    },
)
