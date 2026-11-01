import { test, expect } from "./fixtures";
const routes = [
  "/",
  "/profile",
  "/explorer",
  "/opportunities",
  "/companies",
  "/skills",
  "/roadmap",
  "/resume",
  "/interview",
  "/applications",
  "/monitor",
  "/coach",
  "/notifications",
  "/activity",
  "/settings",
  "/help",
  "/onboarding",
  "/auth/sign-in",
  "/auth/sign-up",
  "/auth/forgot-password",
  "/auth/reset-password",
  "/auth/verify-email",
];
test("all routes render without errors or page overflow", async ({
  page,
}, info) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  for (const route of routes) {
    await page.goto(route);
    await expect(page.locator("h1")).toBeVisible();
    await expect(page.locator("body")).not.toContainText("undefined");
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBeTruthy();
  }
  expect(errors).toEqual([]);
  await page.goto("/");
  await page.screenshot({
    path: `test-results/overview-${info.project.name}.png`,
    fullPage: true,
  });
});
test("profile saves across reloads and roadmap records real actions", async ({
  page,
}) => {
  await page.goto("/profile");
  await page.getByLabel("Full name").fill("Alex Morgan");
  await page.getByLabel("Target role").fill("Frontend Engineer");
  await page.getByLabel("Technical skills").fill("React, CSS");
  await Promise.all([
    page.waitForResponse(
      (response) =>
        response.url().includes("/career-profile") &&
        response.request().method() === "PUT",
    ),
    page.getByRole("button", { name: "Save changes" }).click(),
  ]);
  await page.reload();
  await expect(page.getByLabel("Full name")).toHaveValue("Alex Morgan");
  await page.goto("/roadmap");
  await page
    .getByRole("button", { name: "Review JavaScript fundamentals" })
    .click();
  await expect(page.getByText("1 / 12")).toBeVisible();
  await page.goto("/activity");
  await expect(page.getByText(/Completed learning task/)).toBeVisible();
});
test("discover, compare, save, track and update an application", async ({
  page,
}) => {
  await page.goto("/opportunities");
  await page
    .getByRole("button", { name: "Explore demo content", exact: true })
    .click();
  await expect(page.getByText("Frontend Engineering Intern")).toBeVisible();
  await page.getByLabel("Search opportunities").fill("frontend");
  await expect(page.getByText("Data Science Intern")).toHaveCount(0);
  await page
    .getByRole("button", {
      name: "Save Frontend Engineering Intern",
      exact: true,
    })
    .click();
  await page.getByRole("link", { name: "View details" }).click();
  await page.getByRole("button", { name: "Add to tracker" }).click();
  await page.goto("/applications");
  await expect(
    page.getByRole("button", { name: /Frontend Engineering Intern/ }),
  ).toBeVisible();
  await page
    .getByLabel("Status for Frontend Engineering Intern")
    .selectOption("Interview");
  await page
    .getByRole("button", { name: /Frontend Engineering Intern/ })
    .click();
  await page.getByLabel("Notes").fill("Prepare project walkthrough.");
  await page.getByRole("button", { name: "Save application" }).click();
  await page.reload();
  await expect(
    page.getByLabel("Status for Frontend Engineering Intern"),
  ).toHaveValue("Interview");
});
test("resume editing and interview reflection do not invent AI output", async ({
  page,
}) => {
  await page.goto("/resume");
  await page
    .getByLabel("Resume draft editor")
    .fill("ALEX MORGAN\nSUMMARY\nBuilt accessible interfaces with React.");
  await page.getByRole("button", { name: "Save draft" }).click();
  await page.reload();
  await expect(page.getByLabel("Resume draft editor")).toContainText(
    "ALEX MORGAN",
  );
  await page.goto("/interview");
  await page.getByRole("button", { name: "Start practice" }).click();
  await page
    .getByLabel("Your answer")
    .fill(
      "I would measure rendering performance, identify the slow interaction, and compare the result after a focused change.",
    );
  await page.getByRole("button", { name: "Save & reflect" }).click();
  await expect(page.getByText("Reflection checklist")).toBeVisible();
  await expect(page.getByText(/Static self-review guidance/)).toBeVisible();
});
test("mobile navigation and global search work", async ({ page }, info) => {
  await page.goto("/");
  if (info.project.name === "mobile") {
    await page.getByRole("button", { name: "Open navigation" }).click();
    await page
      .getByRole("link", { name: "Resume Studio", exact: true })
      .click();
    await expect(
      page.getByRole("heading", { name: "Resume Studio", exact: true }),
    ).toBeVisible();
  }
  await page.getByRole("button", { name: /Search anything/ }).click();
  await page.getByPlaceholder("Search pages and tools…").fill("Interview");
  await page
    .getByRole("button", { name: "Interview Lab", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Interview Lab", exact: true }),
  ).toBeVisible();
});
test("onboarding finishes without pretending a live analysis occurred", async ({
  page,
}) => {
  await page.goto("/onboarding");
  await page.getByRole("button", { name: "Let’s get started" }).click();
  await page.getByLabel("Full name").fill("Sam Lee");
  await page.getByRole("button", { name: "Save & continue" }).click();
  await page.getByRole("button", { name: "Save & continue" }).click();
  await page.getByRole("button", { name: "Save & continue" }).click();
  await page.getByRole("button", { name: "Save & continue" }).click();
  await page.getByRole("button", { name: "Save & continue" }).click();
  await page.getByLabel("Target role").fill("Frontend Engineer");
  for (let i = 0; i < 4; i++)
    await page.getByRole("button", { name: "Save & continue" }).click();
  await page.getByRole("button", { name: "Open my workspace" }).click();
  await expect(page.getByRole("heading", { name: /Sam/ })).toBeVisible();
});

test("dashboard reflects saved profile and learning progress without fabricated assessments", async ({
  page,
}) => {
  await page.goto("/profile");
  await page.getByLabel("Full name").fill("Taylor Reed");
  await page.getByLabel("Target role").fill("Frontend Engineer");
  await Promise.all([
    page.waitForResponse(
      (response) =>
        response.url().includes("/career-profile") &&
        response.request().method() === "PUT",
    ),
    page.getByRole("button", { name: "Save changes" }).click(),
  ]);
  await page.goto("/roadmap");
  await page
    .getByRole("button", { name: "Review JavaScript fundamentals" })
    .click();
  await page.goto("/");
  await expect(
    page.getByRole("img", { name: "Profile 25% complete" }),
  ).toBeVisible();
  await expect(page.getByText("1 of 12 tasks complete")).toBeVisible();
  await expect(
    page.getByRole("link", { name: /01 Learning tasks done/ }),
  ).toBeVisible();
  await expect(page.getByText("Resume strength", { exact: true })).toHaveCount(
    0,
  );
});

test("mobile drawer contains keyboard focus and restores its trigger", async ({
  page,
}, info) => {
  test.skip(info.project.name !== "mobile");
  await page.goto("/");
  const trigger = page.getByRole("button", { name: "Open navigation" });
  await trigger.click();
  await expect(
    page.getByRole("button", { name: "Close navigation" }),
  ).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(trigger).toBeFocused();
  await expect(trigger).toHaveAttribute("aria-expanded", "false");
});
