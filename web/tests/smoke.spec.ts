import { expect, test } from "@playwright/test";

/**
 * Smoke tests — verify the app shell, the multi-step wizard, language
 * switching, and the chat input render and behave. These do not require a
 * live backend; the recommend/chat calls may fail gracefully.
 */

test("loads the app shell", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await expect(page.getByText(/System Online|System/i)).toBeVisible();
});

test("profile wizard steps forward", async ({ page }) => {
  await page.goto("/");
  const next = page.getByRole("button", { name: /Next/i });
  await expect(next).toBeVisible();
  await next.click();
  await expect(page.locator("#state")).toBeVisible();
  await next.click();
  await expect(page.getByRole("button", { name: /Run Eligibility Check/i })).toBeVisible();
});

test("language switcher changes locale", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Language" }).click();
  await page.getByRole("option", { name: "हिन्दी" }).click();
  await expect(page.getByText("अपनी योजनाएँ खोजें")).toBeVisible();
});

test("chat consultant opens from the floating button", async ({ page }) => {
  await page.goto("/");
  // Chat is collapsed to a circle by default.
  await page.getByRole("button", { name: /AI Consultant/i }).click();
  await expect(page.getByPlaceholder(/Ask about a scheme/i)).toBeVisible();
});

test("live consultant opens from the header launcher", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /Talk to an Officer/i }).click();
  // The full-screen live overlay shows a type-instead input and end button.
  await expect(page.getByPlaceholder(/type your answer/i)).toBeVisible();
  await expect(page.getByRole("button", { name: /End conversation/i })).toBeVisible();
});
