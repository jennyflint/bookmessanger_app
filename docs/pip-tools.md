### generate requirements.txt based on requirements.in

```bash
docker run --rm -v $(pwd):/api_app -w /api_app python:3.14.1-slim bash -c "pip install pip-tools && pip-compile --upgrade requirements.in"
```

### Install Requirements from requirements.txt

```bash
docker exec api_app pip install -r requirements.txt
```