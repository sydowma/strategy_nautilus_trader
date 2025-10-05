import runpy
import tempfile
import urllib.request

with tempfile.NamedTemporaryFile("wb", suffix=".py", delete=False) as f:
    f.write(urllib.request.urlopen(
    "https://raw.githubusercontent.com/nautechsystems/nautilus_data/main/nautilus_data/hist_data_to_catalog.py"
    ).read())
runpy.run_path(f.name, run_name="__main__")