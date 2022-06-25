from setuptools import find_packages, setup

license = open("LICENSE").read().strip()

setup(
    name="pyfacts",
    version=open("VERSION").read().strip(),
    license=license,
    author="Gourav Kumar",
    author_email="gouravkr@outlook.in",
    url="https://gouravkumar.com",
    description="A library to perform financial analytics on Time Series data",
    long_description=open("README.md").read().strip(),
    packages=find_packages(),
    install_requires=["python-dateutil"],
    test_suite="tests",
)
