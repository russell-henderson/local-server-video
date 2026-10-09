import {test, expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.beforeEach(async ({page}) => {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  (page as any).uiErrors = errors;
  await page.goto('/gallery?sort=name-asc');
  await expect(page.locator('.gallery-item')).toHaveCount(80);
});

test.afterEach(async ({page}) => {
  expect((page as any).uiErrors || []).toEqual([]);
});

test('appends cards, filters motion correctly, restores browser history', async ({page}) => {
  await page.locator('.gallery-item').first().evaluate(element => element.setAttribute('data-preserved', 'yes'));
  await page.getByRole('button', {name:/Load more/}).click();
  await expect(page.locator('[data-preserved=yes]')).toHaveCount(1);
  await expect(page.locator('.gallery-item')).toHaveCount(97);
  await page.locator('[data-filter-pill=motion]').click();
  await expect(page.locator('.gallery-item')).toHaveCount(2);
  await page.locator('[data-filter-pill=webp]').click();
  await expect(page.locator('.gallery-item')).toHaveCount(2);
  await page.goBack();
  await expect(page.locator('[data-image="motion.gif"]')).toHaveCount(1);
  await expect(page.locator('[data-image="static.webp"]')).toHaveCount(0);
});

test('viewer, metadata, focus, originals and local favorites', async ({page}) => {
  const originals: string[] = [];
  page.on('request', request => { if (request.url().includes('/gallery/image/')) originals.push(request.url()); });
  const card = page.getByRole('button', {name:'View image-0000.jpg', exact:true});
  await card.click();
  await expect(page.getByRole('dialog', {name:'Image lightbox viewer'})).toBeVisible();
  await page.getByRole('button', {name:'Toggle Details'}).click();
  await expect(page.locator('#inspectorDimensions')).toHaveText('240 × 360 px');
  expect(originals).toHaveLength(0);
  await page.getByRole('button', {name:'Original resolution', exact:true}).click();
  await expect.poll(() => originals.length).toBe(1);
  await page.locator('#lightboxFavBtn').click();
  await page.getByRole('button', {name:'Close lightbox'}).click();
  await expect(card).toBeFocused();
  await page.locator('[data-filter-pill=favorites]').click();
  await expect(page.locator('.gallery-item')).toHaveCount(1);
  await page.reload();
  await expect(page.locator('.gallery-item')).toHaveCount(1);
});

test('groups can be created, renamed and deleted without deleting media', async ({page, request}, info) => {
  await page.getByRole('button', {name:'Select loaded', exact:true}).click();
  await expect(page.locator('#floatingSelectedCount')).toHaveText('80 selected');
  await page.locator('#floatingCreateGroupBtn').click();
  const name = 'Browser group ' + info.project.name;
  await page.getByLabel('Group name', {exact:true}).fill(name);
  await page.getByRole('dialog').getByRole('button', {name:'Save', exact:true}).click();
  await expect(page.locator('#galleryActionDialog')).not.toBeVisible();
  if (await page.locator('#openGroupsBtn').isVisible()) await page.locator('#openGroupsBtn').click();
  await page.getByLabel('Search groups', {exact:true}).fill(name);
  await page.locator('.organizer-group').filter({hasText:name}).getByRole('button', {name:'Manage',exact:true}).click();
  await page.getByLabel('Group name', {exact:true}).fill(name + ' renamed');
  await page.locator('#galleryActionDialog').getByRole('button', {name:'Save',exact:true}).click();
  await page.locator('.organizer-group').filter({hasText:name + ' renamed'}).getByRole('button', {name:'Manage',exact:true}).click();
  await page.getByRole('button', {name:'Delete group…',exact:true}).click();
  await page.getByRole('button', {name:'Delete group',exact:true}).click();
  await expect(page.locator('#galleryActionDialog')).not.toBeVisible();
  expect((await request.get('/api/gallery')).ok()).toBeTruthy();
  expect((await (await request.get('/api/gallery')).json()).total).toBe(97);
});

test('group detail uses shared renderer and selection', async ({page, request}) => {
  const groups = await (await request.get('/api/gallery/groups')).json();
  const group = groups.find((item:any) => item.name === 'Fixture group');
  await page.goto('/gallery/groups/' + group.slug);
  await expect(page.locator('.gallery-item')).toHaveCount(2);
  await page.getByRole('button', {name:'Select all matching',exact:true}).click();
  await expect(page.locator('#floatingSelectedCount')).toHaveText('2 selected');
});

test('temporary image failures retain cards and offer retry', async ({page}) => {
  await page.route('**/gallery/thumb/**', route => route.abort());
  await page.reload();
  await expect(page.locator('.gallery-item')).toHaveCount(80);
  await expect(page.locator('.image-retry').first()).toBeVisible();
  await page.unroute('**/gallery/thumb/**');
  await page.locator('.image-retry').first().click();
  await expect(page.locator('.image-retry').first()).toBeHidden();
});

test('blocked storage does not break gallery', async ({page}) => {
  await page.addInitScript(() => Object.defineProperty(window, 'localStorage', {get() { throw new Error('blocked'); }}));
  await page.reload();
  await expect(page.locator('.gallery-item')).toHaveCount(80);
});

test('responsive geometry and touch controls', async ({page}) => {
  for (const width of [320, 360, 768, 991, 992, 1024, 1440]) {
    await page.setViewportSize({width,height:800});
    for (const density of ['compact','medium','showcase']) {
      await page.locator('[data-density=' + density + ']').click();
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBeTruthy();
    }
  }
  await page.setViewportSize({width:800,height:360});
  await page.getByRole('button', {name:'View image-0000.jpg',exact:true}).click();
  const close = await page.getByRole('button', {name:'Close lightbox'}).boundingBox();
  expect(close && close.y >= 0 && close.y + close.height <= 360).toBeTruthy();
});

test('gallery accessibility', async ({page}) => {
  const results = await new AxeBuilder({page}).include('.gallery-page-container')
    .withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
  expect(results.violations).toEqual([]);
});

test('approved gallery and viewer states @visual', async ({page}) => {
  await page.evaluate(() => document.fonts.ready);
  await expect(page.locator('.gallery-item img').first()).toHaveJSProperty('complete', true);
  await expect(page).toHaveScreenshot('gallery.png');
  await page.getByRole('button', {name:'View image-0000.jpg',exact:true}).click();
  await expect(page.locator('#lightboxImg')).toHaveJSProperty('complete', true);
  await expect(page).toHaveScreenshot('viewer.png');
  await page.getByRole('button', {name:'Close lightbox'}).click();
  if (await page.locator('#openGroupsBtn').isVisible()) {
    await page.locator('#openGroupsBtn').click();
    await expect(page).toHaveScreenshot('groups-drawer.png');
  }
});
