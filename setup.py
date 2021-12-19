from setuptools import find_packages, setup
import versioneer


with open("README.md", "r", encoding="utf-8") as file:
    long_description = file.read()

setup(
    name="smart_app_framework",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    author="SberDevices",
    author_email="developer@sberdevices.ru",
    description="SmartApp Framework — это фреймворк, "
                "который позволяет создавать смартапы "
                "с поддержкой виртуальных ассистентов Салют.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="sberpl-2",
    packages=find_packages(exclude=[]),
    include_package_data=True,
    install_requires=[
        "aiohttp==3.7.4",
        "aioredis==2.0.0",
        "boto==2.49.0",
        "confluent_kafka==1.7.0",
        "croniter",
        "dawg==0.8.0",
        "dill==0.3.3",
        "ics==0.6",
        "Jinja2==2.10.1",
        "keras==2.6.0",
        "lazy",
        "nltk==3.5",
        "numpy",
        "objgraph==3.4.1",
        "prometheus-client==0.7.1",
        "psutil==5.8.0",
        "pyignite==0.5.2",
        "pymorphy2==0.8",
        "pymorphy2_dicts==2.4.393442.3710985",
        "python-dateutil==2.7.3",
        "python-json-logger==0.1.11",
        "PyYAML==5.3",
        "redis",
        "requests==2.22.0",
        "rusenttokenize==0.0.5",
        "scikit-learn==0.24.1",
        "setuptools",
        "tabulate",
        "tatsu==4.4.0",
        "tensorflow==2.6.0",
        "timeout-decorator==0.4.1",
        "tqdm",
        "Twisted"
    ],
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.9"
    ]
)
