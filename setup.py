from setuptools import find_packages, setup

license = open("LICENSE").read().strip()

setup(
    name="PyFacts",
    version="0.0.1",
    license=license,
    author="Gourav Kumar",
    author_email="gouravkr@outlook.in",
    url="https://gouravkumar.com",
    description="A library which makes handling time series data easier",
    long_description=open("README.md").read().strip(),
    packages=find_packages(),
    install_requires=["python-dateutil"],
    test_suite="tests",
    entry_points={
        "console_scripts": [
            "fincal=fincal.__main__:main",
        ]
    },
)
