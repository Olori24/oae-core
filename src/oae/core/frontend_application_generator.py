from pathlib import Path

from oae.core.project_specification import ProjectSpecification


class FrontendApplicationGenerator:
    """Generate a deterministic Next.js + TypeScript application surface."""

    FRONTEND_ROOT = "web"

    def generate(self, root, specification: ProjectSpecification):
        root = Path(root)
        web = root / self.FRONTEND_ROOT
        files = {
            "package.json": self._package_json(specification),
            "tsconfig.json": self._tsconfig(),
            "next-env.d.ts": self._next_env(),
            "next.config.mjs": "const nextConfig = { reactStrictMode: true };\n\nexport default nextConfig;\n",
            "app/layout.tsx": self._layout(specification),
            "app/page.tsx": self._page(specification),
            "app/globals.css": self._globals(),
            "lib/api.ts": self._api_client(),
            "README.md": self._readme(specification),
            ".gitignore": "node_modules\n.next\nout\n.env.local\n",
        }
        for relative, content in files.items():
            path = web / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        return web

    @staticmethod
    def _package_json(specification):
        return f'''{{
  "name": "{_slug(specification.name)}-web",
  "private": true,
  "version": "0.1.0",
  "scripts": {{
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  }},
  "dependencies": {{
    "next": "^15.5.0",
    "react": "^19.1.0",
    "react-dom": "^19.1.0"
  }},
  "devDependencies": {{
    "@types/node": "^22.15.0",
    "@types/react": "^19.1.0",
    "@types/react-dom": "^19.1.0",
    "typescript": "^5.8.3"
  }}
}}
'''

    @staticmethod
    def _tsconfig():
        return '''{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": false,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{"name": "next"}]
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
'''

    @staticmethod
    def _next_env():
        return '''/// <reference types="next" />
/// <reference types="next/image-types/global" />
'''

    @staticmethod
    def _layout(specification):
        return f'''import "./globals.css";

export const metadata = {{
  title: "{_escape_ts(specification.name)}",
  description: "{_escape_ts(specification.description)}",
}};

export default function RootLayout({{ children }}: Readonly<{{ children: React.ReactNode }}>) {{
  return (
    <html lang="en">
      <body>{{children}}</body>
    </html>
  );
}}
'''

    @staticmethod
    def _page(specification):
        return f'''import {{ getHealth }} from "../lib/api";

export default async function Home() {{
  const health = await getHealth();

  return (
    <main className="shell">
      <section className="hero">
        <span className="eyebrow">OAE GENERATED APPLICATION</span>
        <h1>{_escape_ts(specification.name)}</h1>
        <p>{_escape_ts(specification.description)}</p>
        <div className="status" data-testid="health-status">
          <span className="dot" />
          {{health.status.toUpperCase()}}
        </div>
      </section>
      <section className="panel">
        <div><span className="label">SYSTEM</span><strong>{{health.service}}</strong></div>
        <div><span className="label">FRONTEND</span><strong>Next.js + TypeScript</strong></div>
        <div><span className="label">ENGINE</span><strong>OAE governed build</strong></div>
      </section>
    </main>
  );
}}
'''

    @staticmethod
    def _globals():
        return '''* { box-sizing: border-box; }
html, body { margin: 0; min-height: 100%; }
body {
  color: #f7f9fc;
  background: radial-gradient(circle at 80% 0%, rgba(111,84,255,.22), transparent 32%), #05070c;
  font-family: Inter, ui-sans-serif, system-ui, sans-serif;
}
.shell { width: min(1080px, calc(100% - 32px)); margin: 0 auto; padding: 96px 0; }
.hero { border: 1px solid #1e2a3d; border-radius: 24px; padding: 48px; background: rgba(8,13,22,.88); }
.eyebrow, .label { color: #8292ab; font: 600 11px/1.4 ui-monospace, monospace; letter-spacing: .14em; }
h1 { margin: 12px 0; font-size: clamp(42px, 8vw, 88px); letter-spacing: -.07em; }
p { max-width: 680px; color: #93a0b4; font-size: 17px; line-height: 1.7; }
.status { display: inline-flex; gap: 9px; align-items: center; margin-top: 24px; padding: 10px 14px; border: 1px solid rgba(83,222,167,.25); border-radius: 999px; color: #75e8b6; background: rgba(83,222,167,.06); font: 600 11px ui-monospace, monospace; }
.dot { width: 7px; height: 7px; border-radius: 50%; background: #53dea7; box-shadow: 0 0 16px #53dea7; }
.panel { display: grid; grid-template-columns: repeat(3,1fr); gap: 10px; margin-top: 10px; }
.panel > div { border: 1px solid #1e2a3d; border-radius: 18px; padding: 20px; background: #080d15; }
.panel strong { display: block; margin-top: 8px; font-size: 15px; }
@media (max-width:700px) { .shell { padding: 40px 0; } .hero { padding: 28px; } .panel { grid-template-columns: 1fr; } }
'''

    @staticmethod
    def _api_client():
        return '''export type HealthResult = { status: string; service: string };

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function getHealth(): Promise<HealthResult> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, { cache: "no-store" });
    if (!response.ok) throw new Error(`Health request failed: ${response.status}`);
    return response.json();
  } catch {
    return { status: "degraded", service: "backend-unavailable" };
  }
}
'''

    @staticmethod
    def _readme(specification):
        return f'''# {_escape_md(specification.name)} — generated frontend

Generated by OAE from a project specification.

- Next.js + TypeScript
- Backend boundary: `NEXT_PUBLIC_API_URL`
- Build contract: `npm run build`

This is the governed frontend foundation. Product-specific workflows are added by subsequent engineering missions rather than hidden inside a scaffold.
'''


def _slug(value):
    value = "".join(char.lower() if char.isalnum() else "-" for char in value)
    return "-".join(part for part in value.split("-") if part) or "oae-app"


def _escape_ts(value):
    return str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


def _escape_md(value):
    return str(value).replace("\n", " ")
