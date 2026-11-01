"""Collect torchvision native operators, including the newer _C_stable ABI library."""

from pathlib import Path

from PyInstaller.utils.hooks import get_package_paths

package = Path(get_package_paths("torchvision")[1])
binaries = [(str(path), "torchvision") for path in package.glob("*.so")]
module_collection_mode = "pyz+py"
