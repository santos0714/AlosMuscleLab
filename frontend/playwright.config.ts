import { defineConfig } from "@playwright/test";
import { tmpdir } from "node:os";
import { join } from "node:path";

// La API sirve la interfaz compilada (frontend/dist): ejecutar `npm run build` antes.
// PYTHON: intérprete con las dependencias del backend (por defecto, el .venv del proyecto en
// Windows o `python` en Linux). CHROME_PATH: navegador a usar si no se instaló el de Playwright
// (`npx playwright install chromium`).
const PORT = 8765;
const python =
  process.env.PYTHON ?? (process.platform === "win32" ? "..\\.venv\\Scripts\\python.exe" : "python");
const db = join(tmpdir(), `musclesense_e2e_${Date.now()}.sqlite`);

export default defineConfig({
  testDir: "e2e",
  timeout: 180_000,
  expect: { timeout: 60_000 },
  fullyParallel: false,
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: `http://127.0.0.1:${PORT}`,
    viewport: { width: 1440, height: 1000 },
    launchOptions: process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH, args: ["--no-sandbox"] } : {},
  },
  webServer: {
    command: `"${python}" -m uvicorn musclesense.api.app:app --port ${PORT}`,
    cwd: "../backend",
    env: { MUSCLESENSE_DB: db },
    url: `http://127.0.0.1:${PORT}/api/salud`,
    timeout: 60_000,
    reuseExistingServer: false,
  },
});
