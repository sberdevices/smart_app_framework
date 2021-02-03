from setuptools import find_packages, setup
import versioneer


with open("README.md", "r", encoding='utf-8') as file:
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
        'h5py<3.0.0',
        'tatsu==4.4.0',
        'keras==2.3.1',
        'tensorflow==1.15',
        'nltk',
        'rusenttokenize',
        'rnnmorph',
        "tqdm",
        "tabulate",
        "lazy",
        'setuptools',
        'Jinja2==2.10.1',
        'timeout-decorator==0.4.1',
        'Twisted==19.7.0',
        'confluent_kafka==1.1.0',
        'pymorphy2==0.8',
        'pymorphy2_dicts==2.4.393442.3710985',
        'dawg==0.8.0',
        'python-dateutil==2.7.3',
        'ics==0.6',
        'prometheus-client==0.7.1',
        'boto==2.49.0',
        'pyignite==0.3.4',
        'python-json-logger==0.1.11',
        'PyYAML==5.3',
        'requests==2.22.0',
        'objgraph==3.4.1',
        'psutil==5.6.3',
        'jaeger_client==4.3.0',
        'dill',
        'redis',
        'aiohttp==3.7.3',
        'aioredis',
        'croniter',
    ],
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7'
    ]
)
