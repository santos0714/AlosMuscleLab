import { expect, test, type Page } from "@playwright/test";

const ETAPAS = ["Óptica del tejido", "Transporte de luz", "Fisiología", "Absorción", "Señal óptica", "Electrónica", "Procesado", "Rasgos"];

async function abrir(page: Page) {
  await page.goto("/");
  await expect(page.getByRole("status")).toHaveText("Resultados al día");
}

async function recalculadas(page: Page) {
  return page.locator(".chain .stage.on").allInnerTexts();
}

async function simular(page: Page) {
  await page.getByRole("button", { name: "Simular", exact: true }).click();
  await expect(page.getByRole("status")).toHaveText("Resultados al día");
}

test("calcula el escenario de referencia al abrir", async ({ page }) => {
  const errores: string[] = [];
  page.on("pageerror", (e) => errores.push(String(e)));
  page.on("console", (m) => m.type() === "error" && errores.push(m.text()));
  await abrir(page);
  await expect(page.locator(".chain .stage")).toHaveText(ETAPAS);
  await expect(page.locator(".tissue-svg")).toContainText("% del recorrido");
  await expect(page.locator(".plot .main-svg").first()).toBeVisible();
  for (const vista of ["Fisiología", "Luz y tejido", "Sensor"]) {
    await page.getByRole("tab", { name: vista }).click();
    await expect(page.locator(".plot .main-svg").first()).toBeVisible();
  }
  await expect(page.getByText("Lista de materiales recomendada")).toBeVisible();
  expect(errores).toEqual([]);
});

test("cambiar solo el amplificador recalcula solo la electrónica y lo que sigue", async ({ page }) => {
  await abrir(page);
  await page.getByLabel(/Ganancia del amplificador/).fill("3.3");
  await expect(page.getByRole("status")).toHaveText("Hay cambios sin simular");
  await simular(page);
  expect(await recalculadas(page)).toEqual(["Electrónica", "Procesado", "Rasgos"]);
});

test("la grasa redibuja el corte y obliga a repetir el transporte, no la fisiología", async ({ page }) => {
  await abrir(page);
  await page.getByLabel(/Grasa subcutánea/).first().fill("6.5");
  await expect(page.locator(".tissue-svg")).toContainText("6.5 mm");
  await simular(page);
  const r = await recalculadas(page);
  expect(r).toContain("Transporte de luz");
  expect(r).not.toContain("Fisiología");
});

test("el historial guarda la simulación y la vuelve a cargar", async ({ page }) => {
  await abrir(page);
  await page.getByLabel("Nombre para el historial").fill("prueba e2e");
  await page.getByLabel("Intensidad (% MVC)").fill("35");
  await simular(page);
  await page.getByRole("tab", { name: "Historial" }).click();
  const fila = page.getByRole("row").filter({ hasText: "prueba e2e" });
  await expect(fila).toHaveCount(1);
  await page.reload();
  await expect(page.getByRole("status")).toHaveText("Resultados al día");
  await expect(page.getByLabel("Intensidad (% MVC)")).toHaveValue("50");
  await page.getByRole("tab", { name: "Historial" }).click();
  await page.getByRole("row").filter({ hasText: "prueba e2e" }).getByRole("button", { name: "Cargar" }).click();
  await expect(page.getByLabel("Intensidad (% MVC)")).toHaveValue("35");
  await expect(page.getByLabel("Nombre para el historial")).toHaveValue("prueba e2e");
});

test("un estudio de recuperación pequeño termina y muestra la disociación", async ({ page }) => {
  await abrir(page);
  await page.getByRole("tab", { name: "Recuperación" }).click();
  await page.getByLabel("Sujetos").fill("6");
  await page.getByRole("button", { name: "Iniciar estudio" }).click();
  await expect(page.getByRole("heading", { name: "Reoxigenación frente a recuperación" })).toBeVisible({ timeout: 150_000 });
  await expect(page.getByText("6 sujetos aceptados")).toBeVisible();
  await page.getByRole("button", { name: "30 min" }).click();
  await expect(page.getByText(/En 30 min, .* de los sujetos están reoxigenados/)).toBeVisible();
});
