import site,sys,os
from setuptools import setup

try:
    os.chdir(os.path.split(__file__)[0])
    sys.path.append(os.getcwd())
except Exception:pass
sys.path.extend(site.getsitepackages()+[site.getusersitepackages()])
import pyc_zipper

try:
    long_desc=open("README.rst",encoding="utf-8").read()
except OSError:
    long_desc=""

setup(
    name='pyc-zipper',
    version=pyc_zipper.__version__,
    description=pyc_zipper.__doc__.replace('\n',''),
    long_description=long_desc,
    author="ekcbw",
    author_email="u81430728@163.com",
    url="https://github.com/ekcbw/pyc-zipper",
    packages=["pyc_zipper","pyc_zipper.tests"],
    include_package_data=True,
    keywords=["pyc","bytecode","packer","reverse-engineering","obfuscator","compressor",
              "unpacker","anti-reversing","pyinstaller","压缩","加壳","混淆","脱壳","逆向",
    ],
    classifiers=[
        'Programming Language :: Python',
        "Natural Language :: Chinese (Simplified)",
        "Topic :: Utilities",
        "Topic :: Software Development :: Bug Tracking",
        "Topic :: Software Development :: Debuggers",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ],
    entry_points={
        'console_scripts': [
            'pyc-zipper=pyc_zipper.__main__:main_scripts',
        ],
    },
    install_requires=["pyobject"],
)