# Code Linting
```bash
docker exec api_app ruff check .
```
# Formatting check

```bash
docker exec api_app ruff format --check .
```

# Automatically fix errors that Ruff can handle itself

```bash
docker exec api_app ruff check --fix .
```

# Automatically format code
```bash
docker exec api_app ruff format .
```
# Lint Formatting and fix

```bash
docker exec api_app bash -c "ruff check --fix . && ruff format ."
```