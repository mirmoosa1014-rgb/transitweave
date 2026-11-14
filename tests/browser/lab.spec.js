const { test, expect } = require("@playwright/test");
const fs = require("node:fs/promises");
async function ready(page) {
  await expect(page.locator("#status")).toContainText("Completed:");
  await expect(page.locator("#run")).toBeEnabled();
}
test("generate, compare, fold, reveal and export actual results", async ({
  page,
}) => {
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await ready(page);
  await expect(
    page.getByRole("heading", { name: "FIND THE REPEAT." }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Raw baseline" }).click();
  await expect(page.locator("#raw")).toHaveAttribute("aria-pressed", "true");
  await page
    .getByRole("button", { name: "Detrended search", exact: true })
    .click();
  await page.locator("#trial").fill("120");
  await expect(page.locator("#trial-output")).toHaveText("2.600 days");
  await page.locator("#reveal").check();
  await expect(page.locator("#truth")).toContainText("EVALUATOR ONLY");
  await page.locator("#best").click();
  const downloadPromise = page.waitForEvent("download");
  await page.locator("#export").click();
  const download = await downloadPromise;
  const record = JSON.parse(await fs.readFile(await download.path(), "utf8"));
  expect(record.truth.seed).toBe(3001);
  await expect(page.locator("#timeline circle")).toHaveCount(
    record.time.length,
  );
  expect(record.methods.raw.scores.length).toBe(421);
  await page.locator("#family").selectOption("gapped");
  await page.locator("#depth").selectOption("0");
  await page.locator("#seed").fill("4001");
  await page.locator("#run").click();
  await ready(page);
  await expect(page.locator("#status")).toContainText("seed 4001");
  await expect(page.locator("#truth")).toContainText("no-transit control");
  expect(errors).toEqual([]);
  await page.locator("#family").selectOption("variable");
  await page.locator("#depth").selectOption("1200");
  await page.locator("#seed").fill("3001");
  await page.locator("#run").click();
  await ready(page);
  await page.locator("#reveal").uncheck();
  await page.screenshot({
    path: "docs/images/app-desktop.png",
    fullPage: true,
    animations: "disabled",
  });
});
test("mobile layout and reduced motion remain usable", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await ready(page);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  await expect(page.locator(".draw")).toHaveCSS("animation-name", "none");
  await page.locator("#trial").focus();
  await page.keyboard.press("ArrowRight");
  await expect(page.locator("#trial-output")).not.toHaveText("—");
  await page.screenshot({
    path: "docs/images/app-mobile.png",
    fullPage: true,
    animations: "disabled",
  });
});
test("failed simulation cannot export an old case", async ({ page }) => {
  await page.goto("/");
  await ready(page);
  await page.route("**/api/run", (route) =>
    route.fulfill({
      status: 400,
      contentType: "application/json",
      body: JSON.stringify({ error: "Controlled failure" }),
    }),
  );
  await page.locator("#run").click();
  await expect(page.getByRole("alert")).toHaveText("Controlled failure");
  await expect(page.locator("#export")).toBeDisabled();
  await expect(page.locator("#run")).toBeEnabled();
});
