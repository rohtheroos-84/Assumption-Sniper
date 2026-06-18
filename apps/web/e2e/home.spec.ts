import { test, expect } from '@playwright/test'

test.describe('home workflow', () => {
  test('shows idea input and empty run state', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByRole('heading', { name: /assumption sniper/i })).toBeVisible()
    await expect(page.getByLabel(/idea \/ hypothesis/i)).toBeVisible()
    await expect(page.getByRole('button', { name: /start run/i })).toBeVisible()
    await expect(page.getByText('No active run')).toBeVisible()
  })

  test('does not call api when submitting empty idea', async ({ page }) => {
    let createCalled = false
    await page.route('**/api/v1/runs', async (route) => {
      createCalled = true
      await route.fulfill({ status: 201, body: JSON.stringify({ id: 'run-e2e' }) })
    })

    await page.goto('/')
    await page.getByRole('button', { name: /start run/i }).click()
    expect(createCalled).toBe(false)
  })

  test('creates and starts a run from idea input', async ({ page }) => {
    await page.route('**/api/v1/runs', async (route) => {
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'run-e2e-1', status: 'queued' }),
      })
    })
    await page.route('**/api/v1/runs/run-e2e-1/start', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ run_id: 'run-e2e-1', status: 'queued' }),
      })
    })
    await page.route('**/api/v1/runs/run-e2e-1/events', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: 'data: {"message":"pipeline queued"}\n\n',
      })
    })

    await page.goto('/')
    await page.getByLabel(/idea \/ hypothesis/i).fill('AI tutor for high school math')
    await page.getByRole('button', { name: /start run/i }).click()

    await expect(page.getByText(/Run: run-e2e-1/)).toBeVisible()
    await expect(page.getByText(/status: queued/i)).toBeVisible()
  })
})
