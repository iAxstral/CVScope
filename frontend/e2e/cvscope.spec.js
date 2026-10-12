import { expect, test } from "@playwright/test";
import { fileURLToPath } from "node:url";

const CV_PDF = fileURLToPath(
  new URL("../../backend/tests/archivos/cv_ejemplo.pdf", import.meta.url),
);

async function iniciarSesion(page) {
  await page.goto("/");
  await page.getByLabel("Email").fill("admin@cvscope.co");
  await page.getByLabel("Contraseña").fill("cvscope2026");
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page).toHaveURL(/\/dashboard$/);
}

async function abrirMenuSiEsMovil(page) {
  const menu = page.getByRole("button", { name: "Abrir menú de navegación" });
  if (await menu.isVisible()) await menu.click();
}

test("sin sesión se pide iniciar sesión y se rechaza una clave incorrecta", async ({ page }) => {
  await page.goto("/ranking/1");
  await expect(page).toHaveURL(/\/$/);
  await page.getByLabel("Email").fill("admin@cvscope.co");
  await page.getByLabel("Contraseña").fill("incorrecta");
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page.getByRole("alert")).toContainText("Correo o contraseña incorrectos");
});

test("tras iniciar sesión se vuelve a la página pedida y se puede cerrar sesión", async ({
  page,
}) => {
  await page.goto("/datasets");
  await page.getByLabel("Email").fill("admin@cvscope.co");
  await page.getByLabel("Contraseña").fill("cvscope2026");
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page).toHaveURL(/\/datasets$/);
  await abrirMenuSiEsMovil(page);
  await page.getByRole("button", { name: "Cerrar sesión" }).click();
  await expect(page).toHaveURL(/\/$/);
});

test("el dashboard muestra los roles y permite crear uno nuevo", async ({ page }, info) => {
  await iniciarSesion(page);
  await expect(page.getByRole("heading", { name: "Full Stack Developer" })).toBeVisible();
  expect(await page.locator(".role-card").count()).toBeGreaterThanOrEqual(4);

  const nombre = `Rol de prueba ${info.project.name}`;
  await page.getByRole("button", { name: "+ Nuevo rol" }).click();
  await page.getByLabel("Nombre del rol").fill(nombre);
  await page.getByLabel(/Requisitos mínimos/).fill("Python\nSQL");
  await page.getByRole("button", { name: "Crear rol" }).click();
  await expect(page.getByRole("heading", { name: nombre })).toBeVisible();
});

test("el ranking muestra el top 5 de la red y se puede comparar con palabras clave", async ({
  page,
}) => {
  await iniciarSesion(page);
  await page.goto("/ranking/1");
  await expect(page.locator(".ranking-row")).toHaveCount(5);
  await expect(page.getByText("Fuerza red").first()).toBeVisible();
  await page.getByRole("tab", { name: "Palabras clave" }).click();
  await expect(page).toHaveURL(/metodo=palabras_clave/);
  await expect(page.locator(".ranking-row")).toHaveCount(5);
});

test("seleccionar un CV de ejemplo muestra el veredicto con evidencia y el de la LVQ", async ({
  page,
}) => {
  await iniciarSesion(page);
  await page.goto("/seleccionar?rolId=1");
  await page.getByRole("button", { name: "Usar CV de ejemplo" }).click();
  await page.getByRole("button", { name: "Evaluar hoja de vida" }).click();
  await expect(page.locator(".sel-summary")).toContainText("Full Stack Developer");
  await expect(page.locator(".sel-summary__lvq")).toContainText("LVQ:");
  await expect(page.locator(".req-item")).toHaveCount(4);
});

test("al subir un PDF se extrae su texto", async ({ page }) => {
  await iniciarSesion(page);
  await page.goto("/seleccionar?rolId=1");
  await page.locator('input[type="file"]').setInputFiles(CV_PDF);
  await expect(page.getByText(/Texto extraído \(\d+ caracteres\)/)).toBeVisible();
  await expect(page.getByLabel(/Texto del CV/)).toHaveValue(/TypeScript, React y Node\.js/);
});

test("la red competitiva juega el torneo, la competencia abierta y un duelo", async ({ page }) => {
  await iniciarSesion(page);
  await page.goto("/torneo/2");
  await expect(page.locator(".torneo-campeon__nombre")).not.toBeEmpty();
  await expect(page.locator(".torneo-podio li")).toHaveCount(5);
  await expect(page.locator(".bracket-match").first()).toBeVisible();
  await expect(page.locator(".torneo-abierta svg")).toBeVisible();
  await expect(page.locator(".lvq-panel")).toContainText("Exactitud en prueba");

  await page.getByRole("button", { name: "Enfrentar" }).click();
  await expect(page.locator(".duelo-esquina__badge")).toHaveText("Gana");
  await expect(page.locator(".duelo__maxnet svg")).toBeVisible();
});

test("ninguna página se desborda horizontalmente", async ({ page }) => {
  await iniciarSesion(page);
  for (const ruta of ["/dashboard", "/seleccionar", "/ranking/1", "/torneo/1", "/datasets"]) {
    await page.goto(ruta);
    await page.waitForLoadState("networkidle");
    const ancho = await page.evaluate(
      () => document.documentElement.scrollWidth - window.innerWidth,
    );
    expect(ancho, `desborde en ${ruta}`).toBeLessThanOrEqual(0);
  }
});
