import {test, expect} from '@playwright/test';

test('navigation and actual video playback', async ({page}) => {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/');
  if (await page.getByRole('button', {name:'Toggle navigation'}).isVisible()) {
    await page.getByRole('button', {name:'Toggle navigation'}).click();
  }
  await page.locator('#main-nav').getByRole('link', {name:'Gallery',exact:true}).click();
  await expect(page.locator('#galleryGrid')).toBeVisible();
  await page.goto('/watch/fixture.mp4');
  const video = page.locator('[data-player] video');
  await expect.poll(() => video.evaluate((v:HTMLVideoElement) => v.readyState)).toBeGreaterThanOrEqual(2);
  await page.locator('[data-action=play]').click();
  await expect.poll(() => video.evaluate((v:HTMLVideoElement) => v.currentTime)).toBeGreaterThan(0);
  await page.locator('[data-action=play]').click();
  await page.locator('[data-role=seek]').fill('50');
  await expect.poll(() => video.evaluate((v:HTMLVideoElement) => v.currentTime)).toBeGreaterThan(1);
  expect(errors).toEqual([]);
});
