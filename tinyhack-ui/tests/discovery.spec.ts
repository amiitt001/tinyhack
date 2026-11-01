import { test as base, expect } from "@playwright/test";
import { jobs, mockBackend, RUN_ID, type MockOptions } from "./fixtures";

base(
  "unavailable sources explain the next step and keep discovery disabled",
  async ({ page }) => {
    const api = await mockBackend(page);
    await page.goto("/opportunities");
    await expect(
      page.getByRole("heading", { name: "Discovery sources aren’t ready yet" }),
    ).toHaveCount(0); // Notices use text, not fake page headings.
    await expect(
      page.getByText("Discovery sources aren’t ready yet"),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Discover opportunities", exact: true }),
    ).toBeDisabled();
    await page.getByRole("button", { name: "Source availability" }).click();
    await expect(
      page.getByRole("dialog", { name: "Discovery sources" }),
    ).toBeVisible();
    await expect(page.getByText("Setup needed")).toBeVisible();
    await expect(page.getByText("Restricted", { exact: true })).toHaveCount(3);
    await page.keyboard.press("Escape");
    await expect(
      page.getByRole("button", { name: "Source availability" }),
    ).toBeFocused();
    expect(api.created).toBe(false);
  },
);

base(
  "source connection failures can recover without creating a search",
  async ({ page }) => {
    const options: MockOptions = { source: "offline" };
    const api = await mockBackend(page, options);
    await page.goto("/opportunities");
    await expect(
      page.getByText("We couldn’t connect to discovery"),
    ).toBeVisible();
    await expect(
      page.getByText(
        "The backend is unavailable. Check your connection and try again.",
      ),
    ).toBeVisible();
    options.source = "configured";
    await page.getByRole("button", { name: "Try again", exact: true }).click();
    await expect(
      page.getByText("Discovery sources aren’t ready yet"),
    ).toBeVisible();
    expect(api.created).toBe(false);
  },
);

base(
  "live opportunities compare three at a time with reversible selection",
  async ({ page }) => {
    await mockBackend(page, { source: "enabled" });
    await page.goto(`/opportunities?run=${RUN_ID}`);
    const cards = page.locator(".opportunity-card");
    await expect(cards).toHaveCount(6);
    for (let index = 0; index < 3; index++)
      await cards
        .nth(index)
        .getByRole("checkbox", { name: "Compare", exact: true })
        .check();
    await page
      .getByRole("button", { name: "Compare opportunities", exact: true })
      .click();
    const dialog = page.getByRole("dialog", {
      name: "Compare opportunities",
      exact: true,
    });
    await expect(
      dialog.getByRole("heading", {
        name: "Python Developer Intern",
        exact: true,
      }),
    ).toBeVisible();
    await expect(
      dialog.getByText("Compensation not listed", { exact: true }),
    ).toHaveCount(2);
    await dialog
      .getByRole("button", {
        name: "Remove Python Developer Intern from comparison",
      })
      .click();
    await expect(
      dialog.getByRole("heading", {
        name: "Python Developer Intern",
        exact: true,
      }),
    ).toHaveCount(0);
    await page.keyboard.press("Escape");
    await cards
      .nth(0)
      .getByRole("checkbox", { name: "Compare", exact: true })
      .check();
    await cards
      .nth(3)
      .getByRole("checkbox", { name: "Compare", exact: true })
      .click();
    await expect(
      cards.nth(3).getByRole("checkbox", { name: "Compare", exact: true }),
    ).not.toBeChecked();
    await expect(
      page
        .getByRole("status")
        .filter({ hasText: "Compare up to three opportunities at a time." }),
    ).toBeVisible();
  },
);

base(
  "discovery progresses to partial results, supports details and a server-backed shortlist",
  async ({ page }, info) => {
    const api = await mockBackend(page, {
      source: "enabled",
      statuses: ["pending", "running", "partially_completed"],
    });
    await page.goto("/opportunities");
    await page
      .getByLabel("Search opportunities")
      .fill("Python Developer Intern");
    await page.getByLabel("Location", { exact: false }).fill("Delhi NCR");
    await page.getByLabel("Employment type").selectOption("internship");
    await page
      .getByRole("button", { name: "Discover opportunities", exact: true })
      .click();
    await expect(
      page.getByRole("heading", { name: "Your search is queued" }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Some opportunities are ready" }),
    ).toBeVisible();
    await expect(page.locator(".opportunity-card")).toHaveCount(6);
    expect(api.keys).toHaveLength(1);
    expect(api.input?.sources).toEqual(["official_company_careers"]);
    expect(api.input?.location).toBe("Delhi NCR");
    expect(api.input?.employment_type).toBe("internship");
    const first = page.locator(".opportunity-card").first();
    await first.getByRole("link", { name: "View details" }).click();
    const dialog = page.getByRole("dialog", {
      name: "Python Developer Intern",
      exact: true,
    });
    await expect(dialog).toBeVisible();
    await expect(dialog.getByText(/MONTH|month/)).toBeVisible();
    await expect(
      dialog.getByRole("link", { name: "View application page" }),
    ).toHaveAttribute("href", jobs[0].application_url!);
    await page.screenshot({
      path: `test-results/discovery-drawer-${info.project.name}.png`,
      fullPage: true,
    });
    await page.keyboard.press("Escape");
    await expect(
      first.getByRole("link", { name: "View details" }),
    ).toBeFocused();
    await first
      .getByRole("button", {
        name: "Save Python Developer Intern",
        exact: true,
      })
      .click();
    await expect(
      first.getByRole("button", {
        name: "Unsave Python Developer Intern",
        exact: true,
      }),
    ).toBeVisible();
    await page.getByRole("tab", { name: /Saved/ }).click();
    await expect(page.locator(".opportunity-card")).toHaveCount(1);
    await page.reload();
    await expect(page.locator(".opportunity-card")).toHaveCount(1);
    await page
      .getByRole("button", {
        name: "Unsave Python Developer Intern",
        exact: true,
      })
      .click();
    await expect(
      page.getByRole("heading", { name: "Your shortlist starts here." }),
    ).toBeVisible();
  },
);

base(
  "results pagination and detail close preserve the result page",
  async ({ page }, info) => {
    await mockBackend(page, { source: "enabled" });
    await page.goto(`/opportunities?run=${RUN_ID}&q=Python`);
    await expect(page.locator(".opportunity-card")).toHaveCount(6);
    await page.getByRole("button", { name: "Next opportunities page" }).click();
    await expect(page.locator(".opportunity-card")).toHaveCount(1);
    await expect(page).toHaveURL(/page=2/);
    await page.getByRole("link", { name: "View details" }).click();
    await expect(page.getByRole("dialog")).toBeVisible();
    await page.getByRole("button", { name: "Close dialog" }).click();
    await expect(page).toHaveURL(/page=2/);
    await expect(page.locator(".opportunity-card")).toHaveCount(1);
    await page
      .getByRole("button", { name: "Previous opportunities page" })
      .click();
    await expect(page.locator(".opportunity-card")).toHaveCount(6);
    await page.screenshot({
      path: `test-results/discovery-results-${info.project.name}.png`,
      fullPage: true,
    });
  },
);

base(
  "an interrupted creation retries with the same idempotency key",
  async ({ page }) => {
    const api = await mockBackend(page, {
      source: "enabled",
      createFailure: true,
      singleJob: true,
    });
    await page.goto("/opportunities");
    await page.getByLabel("Search opportunities").fill("Python Intern");
    const submit = page.getByRole("button", {
      name: "Discover opportunities",
      exact: true,
    });
    await submit.click();
    await expect(
      page.getByText(
        "The backend is unavailable. Check your connection and try again.",
      ),
    ).toBeVisible();
    await submit.click();
    await expect(page.locator(".opportunity-card")).toHaveCount(1);
    expect(api.keys).toHaveLength(2);
    expect(api.keys[0]).toBe(api.keys[1]);
  },
);

base(
  "structured errors and save failures remain readable and do not invent success",
  async ({ page }) => {
    const api = await mockBackend(page, {
      source: "enabled",
      savedFailure: true,
      singleJob: true,
    });
    await page.goto(`/opportunities?run=${RUN_ID}`);
    const save = page.getByRole("button", {
      name: "Save Python Developer Intern",
      exact: true,
    });
    await save.click();
    await expect(
      page
        .getByRole("status")
        .filter({ hasText: "Saving is temporarily unavailable." }),
    ).toBeVisible();
    await expect(save).toBeVisible();
    expect(api.saved.size).toBe(0);
  },
);

base(
  "authentication and service failures have distinct recovery messages",
  async ({ page }) => {
    await mockBackend(page, { source: "unauthorized" });
    await page.goto("/opportunities");
    await expect(
      page.getByText("Your session has expired. Sign in to continue."),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Discover opportunities", exact: true }),
    ).toBeDisabled();
  },
);

base(
  "failed discoveries stop polling and offer a fresh search",
  async ({ page }) => {
    const api = await mockBackend(page, {
      source: "enabled",
      statuses: ["failed"],
    });
    await page.goto(`/opportunities?run=${RUN_ID}`);
    await expect(
      page.getByRole("heading", { name: "This search couldn’t be completed" }),
    ).toBeVisible();
    await expect(page.getByLabel("Discovery stages")).toHaveCount(0);
    await expect(
      page.getByRole("button", { name: "Discover opportunities", exact: true }),
    ).toBeEnabled();
    const reads = api.reads;
    await page.waitForTimeout(1700);
    expect(api.reads).toBe(reads);
  },
);

base(
  "result retrieval errors can be retried without another discovery request",
  async ({ page }) => {
    const api = await mockBackend(page, {
      source: "enabled",
      resultFailure: true,
      singleJob: true,
    });
    // A terminal response also causes one authoritative result refresh.
    await page.goto(`/opportunities?run=${RUN_ID}`);
    if (await page.getByRole("button", { name: "Retry results" }).isVisible())
      await page.getByRole("button", { name: "Retry results" }).click();
    await expect(page.locator(".opportunity-card")).toHaveCount(1);
    expect(api.keys).toHaveLength(0);
  },
);

base("direct detail pages hide expired application links", async ({ page }) => {
  await mockBackend(page, { source: "enabled", expired: true });
  await page.goto(`/opportunities/${jobs[0].id}`);
  await expect(
    page.getByRole("heading", { name: jobs[0].title, exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText(
      "This listing may be out of date. Review the original source.",
    ),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "View application page" }),
  ).toHaveCount(0);
});

base(
  "responsive discovery stays within the page and mobile navigation returns focus",
  async ({ page }) => {
    await mockBackend(page, { source: "enabled" });
    await page.goto(`/opportunities?run=${RUN_ID}`);
    for (const width of [320, 375, 768, 1024, 1440]) {
      await page.setViewportSize({ width, height: 900 });
      await expect(page.locator(".opportunity-card").first()).toBeVisible();
      const layout = await page.evaluate(() => ({
        viewport: innerWidth,
        width: document.documentElement.scrollWidth,
        overflowing: [...document.querySelectorAll("main *")]
          .filter(
            (element) => element.getBoundingClientRect().right > innerWidth,
          )
          .map((element) => ({
            className: element.className,
            right: Math.round(element.getBoundingClientRect().right),
          })),
      }));
      await page.screenshot({ path: `test-results/discovery-${width}.png` });
      expect(layout.width, JSON.stringify(layout)).toBeLessThanOrEqual(width);
    }
    await page.setViewportSize({ width: 375, height: 844 });
    const nav = page.getByRole("navigation", { name: "Quick navigation" });
    await expect(nav).toBeVisible();
    await nav.getByRole("button", { name: "More navigation" }).click();
    await page.keyboard.press("Escape");
    await expect(
      nav.getByRole("button", { name: "More navigation" }),
    ).toBeFocused();
    const preferences = page.getByRole("button", {
      name: "Refine your search",
      exact: true,
    });
    await preferences.click();
    await expect(page.getByLabel("Search opportunities")).toBeVisible();
    await page
      .getByRole("button", { name: "Your search preferences", exact: true })
      .click();
    await expect(page.getByLabel("Search opportunities")).toBeHidden();
  },
);

base(
  "resume preview reflects the draft and reports unsaved edits",
  async ({ page }) => {
    await mockBackend(page);
    await page.goto("/resume");
    await page
      .getByLabel("Resume draft editor")
      .fill("TAYLOR REED\nSUMMARY\nBuilt accessible React interfaces.");
    await expect(
      page.getByText("Unsaved changes", { exact: true }),
    ).toBeVisible();
    await page.getByRole("button", { name: "Preview", exact: true }).click();
    await expect(page.getByLabel("Resume preview")).toContainText(
      "Built accessible React interfaces.",
    );
    await page
      .getByRole("button", { name: "Save draft", exact: false })
      .click();
    await expect(
      page.getByText("Saved locally", { exact: true }),
    ).toBeVisible();
    await page.getByRole("button", { name: "Edit", exact: true }).click();
    await expect(page.getByLabel("Resume draft editor")).toHaveValue(
      "TAYLOR REED\nSUMMARY\nBuilt accessible React interfaces.",
    );
  },
);
