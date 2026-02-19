# Pulumi task setup (Yandex Cloud)

## 1) Prepare project

```bash
cd pulumi
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp Pulumi.dev.example.yaml Pulumi.dev.yaml
#fill Pulumi.dev.yaml with real values
```

If you see `ModuleNotFoundError: No module named 'pkg_resources'`, run:

```bash
python -m pip install --upgrade "setuptools<81"
```

## 2) Preview and apply

```bash
pulumi login
pulumi stack init dev
pulumi preview
pulumi up
pulumi stack output
```

## 3) Verify SSH

```bash
ssh $(pulumi stack output ssh_command | sed 's/"//g' | sed 's/^ssh //')
```

## 4) Cleanup

```bash
pulumi destroy
```