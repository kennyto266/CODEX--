#!/usr/bin/env python3
import os, json, yaml, argparse
from datetime import datetime
from pathlib import Path
from importlib import import_module
import requests
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

class APIDocGenerator:
    def __init__(self, app, output_dir, base_url="http://localhost:8001"):
        self.app_path = app
        self.output_dir = Path(output_dir)
        self.base_url = base_url
        self.api_url = f"{base_url}/openapi.json"
        self.docs_dir = self.output_dir / "api"
        self.examples_dir = self.output_dir / "examples"
        for d in [self.docs_dir, self.examples_dir]:
            d.mkdir(parents=True, exist_ok=True)
        self.openapi_spec = None
        self.api_routes = []

    def load_openapi_spec(self):
        try:
            r = requests.get(self.api_url, timeout=5)
            r.raise_for_status()
            self.openapi_spec = r.json()
        except:
            try:
                path, name = self.app_path.rsplit(".", 1) if "." in self.app_path else ("__main__", self.app_path)
                module = import_module(path)
                app = getattr(module, name) if name else module
                if isinstance(app, FastAPI):
                    self.openapi_spec = get_openapi(title=app.title, version=app.version,
                        openapi_version=app.openapi_version, description=app.description, routes=app.routes)
            except Exception as e:
                raise Exception(f"Failed: {e}")

    def extract_api_routes(self):
        if not self.openapi_spec:
            self.load_openapi_spec()
        routes = []
        for path, methods in self.openapi_spec.get("paths", {}).items():
            for method, details in methods.items():
                if method.upper() not in ["HEAD", "OPTIONS"]:
                    routes.append({
                        "path": path, "method": method.upper(),
                        "summary": details.get("summary", ""),
                        "description": details.get("description", ""),
                        "parameters": details.get("parameters", []),
                        "responses": details.get("responses", {})
                    })
        self.api_routes = routes
        return routes

    def generate_all(self):
        self.load_openapi_spec()
        self.extract_api_routes()
        results = {}
        results["openapi_yaml"] = self.generate_openapi_yaml()
        results["openapi_json"] = self.generate_openapi_json()
        results["reference_md"] = self.generate_markdown_reference()
        results["reference_html"] = self.generate_html_documentation()
        results["interactive"] = self.generate_interactive_docs()
        results["examples"] = self.extract_code_examples()
        results["index"] = self.create_index_page()
        return results

    def generate_openapi_yaml(self):
        if not self.openapi_spec:
            self.load_openapi_spec()
        f = self.docs_dir / "openapi.yaml"
        yaml.dump(self.openapi_spec, open(f, "w"), default_flow_style=False, allow_unicode=True)
        return f

    def generate_openapi_json(self):
        if not self.openapi_spec:
            self.load_openapi_spec()
        f = self.docs_dir / "openapi.json"
        json.dump(self.openapi_spec, open(f, "w"), indent=2, ensure_ascii=False)
        return f

    def generate_markdown_reference(self):
        if not self.api_routes:
            self.extract_api_routes()
        content = f"# {self.openapi_spec.get('info', {}).get('title', 'API Reference')}\n\n"
        content += f"Version: {self.openapi_spec.get('info', {}).get('version', '')}\n\n"
        content += f"{self.openapi_spec.get('info', {}).get('description', '')}\n\n"
        content += "## Endpoints\n\n"
        for route in self.api_routes:
            content += f"### {route['method']} {route['path']}\n\n"
            content += f"{route['summary']}\n\n"
            if route['description']:
                content += f"{route['description']}\n\n"
            content += "---\n\n"
        f = self.docs_dir / "reference.md"
        open(f, "w").write(content)
        return f

    def generate_html_documentation(self):
        if not self.api_routes:
            self.extract_api_routes()
        html = f"""<!DOCTYPE html>
<html><head><title>{self.openapi_spec.get('info', {}).get('title', 'API Documentation')}</title>
<style>
body {{font-family: Arial, sans-serif; margin: 40px; line-height: 1.6;}}
h1,h2,h3 {{color: #2c3e50;}} 
code {{background:#f4f4f4; padding:2px 4px; border-radius:3px;}}
table {{border-collapse: collapse; width: 100%;}} 
th,td {{border:1px solid #ddd; padding:8px;}}
th {{background: #4CAF50; color:white;}}
</style>
</head><body>
<h1>{self.openapi_spec.get('info', {}).get('title', 'API Reference')}</h1>
<p>Version: {self.openapi_spec.get('info', {}).get('version', '')}</p>
<h2>Endpoints</h2>
"""
        for route in self.api_routes:
            html += f'<h3>{route["method"]} {route["path"]}</h3><p>{route["summary"]}</p>'
        html += "</body></html>"
        f = self.docs_dir / "index.html"
        open(f, "w").write(html)
        return f

    def generate_interactive_docs(self):
        html = f"""<!DOCTYPE html>
<html><head>
<title>{self.openapi_spec.get('info', {}).get('title', 'API')}</title>
<link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui.css">
</head><body>
<div id="swagger-ui"></div>
<script src="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui-bundle.js"></script>
<script>
SwaggerUIBundle({{url: '{self.api_url}', dom_id: '#swagger-ui'}});
</script>
</body></html>"""
        f = self.docs_dir / "swagger.html"
        open(f, "w").write(html)
        return f

    def extract_code_examples(self):
        if not self.api_routes:
            self.extract_api_routes()
        py = f"""import requests
BASE_URL = "{self.base_url}"

class APIClient:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
    
    def get(self, endpoint, params=None):
        r = requests.get(f"{self.base_url}{{endpoint}}", params=params)
        r.raise_for_status()
        return r.json()
    
    def post(self, endpoint, data=None):
        r = requests.post(f"{self.base_url}{{endpoint}}", json=data)
        r.raise_for_status()
        return r.json()
"""
        open(self.examples_dir / "example_python.py", "w").write(py)
        sh = "#!/bin/bash\n"
        for r in self.api_routes[:5]:
            sh += f'# {r["summary"]}\n'
            sh += f'curl -X {r["method"]} "{self.base_url}{r["path"]}"\n\n'
        open(self.examples_dir / "example_curl.sh", "w").write(sh)
        return self.examples_dir

    def create_index_page(self):
        html = f"""<!DOCTYPE html>
<html><head>
<title>{self.openapi_spec.get('info', {}).get('title', 'API Docs')}</title>
<style>
body {{font-family: Arial, sans-serif; margin:40px;}}
.header {{background:#2c3e50; color:white; padding:20px; border-radius:5px;}}
.card {{border:1px solid #ddd; padding:20px; margin:10px 0; border-radius:5px;}}
.button {{background:#4CAF50; color:white; padding:10px 20px; text-decoration:none; border-radius:5px;}}
a {{color:#4CAF50;}}
</style>
</head><body>
<div class="header">
<h1>{self.openapi_spec.get('info', {}).get('title', 'API Documentation')}</h1>
<p>Version: {self.openapi_spec.get('info', {}).get('version', '')}</p>
<p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
</div>

<h2>Documentation</h2>

<div class="card">
<h3>API Reference</h3>
<p>Complete API reference with all endpoints</p>
<a class="button" href="api/index.html">View API Reference</a>
</div>

<div class="card">
<h3>Interactive Documentation</h3>
<p>Try out the API with Swagger UI</p>
<a class="button" href="api/swagger.html">Open Swagger UI</a>
</div>

<div class="card">
<h3>OpenAPI Specification</h3>
<p>Raw OpenAPI YAML and JSON files</p>
<a href="api/openapi.yaml">YAML</a> | <a href="api/openapi.json">JSON</a>
</div>

<div class="card">
<h3>Code Examples</h3>
<p>Client libraries and usage examples</p>
<a href="examples/example_python.py">Python</a> | <a href="examples/example_curl.sh">cURL</a>
</div>

</body></html>"""
        f = self.output_dir / "index.html"
        open(f, "w").write(html)
        return f

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Generate API documentation")
    p.add_argument("--app", default="api_server:app")
    p.add_argument("--output", default="docs")
    p.add_argument("--base-url", default="http://localhost:8001")
    args = p.parse_args()
    
    gen = APIDocGenerator(args.app, args.output, args.base_url)
    res = gen.generate_all()
    
    print("\nGenerated Files:")
    for k, v in res.items():
        print(f"{k:20s} {v}")
