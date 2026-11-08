# Editable Installation Evidence

- The documented `python -m pip install -e ".[dev]"` first failed because pip 24.0 could not validate the package-index certificate (`SSLCertVerificationError: unable to get local issuer certificate`). Retrying with the host certifi bundle and pip's truststore feature did not resolve the certificate error.
- An offline pip attempt then failed because the preinstalled setuptools 65.5.0 lacked the `bdist_wheel` command. This failure is summarized here; its raw stderr was not saved before recovery.
- Recovery: `uv pip install --system-certs --cache-dir .cache\uv --python .\.venv\Scripts\python.exe -e ".[dev]"` succeeded and installed the editable package, Ruff, and Bandit.
- Recovery: `uv pip install --system-certs --cache-dir .cache\uv --python .\.venv\Scripts\python.exe --upgrade pip setuptools wheel` upgraded the venv build tools to pip 26.3, setuptools 84.2.1, and wheel 0.48.0.
- The documented pip command was then rerun and succeeded: `.\.venv\Scripts\python.exe -m pip install -e ".[dev]"`. Import verification resolved `alert_manager` to `src\alert_manager\__init__.py`.

The initial failures are recorded here as a summary; they were not presented as successful installation results.
