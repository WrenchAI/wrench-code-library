from setuptools import setup, find_packages

setup(
    name='wrench-code-library',
    version='0.1.0',
    author='willem@wrench.ai',
    packages=find_packages(),
    install_requires=[
        'colorama~=0.4.6',
        'pandas~=1.5.3',
        'requests~=2.29.0',
        'psycopg2~=2.9.6',
        'python-dotenv~=1.0.0',
        'openai~=0.27.4',
        'tenacity~=8.2.2',
    ],
)
