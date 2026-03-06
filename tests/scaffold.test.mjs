import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const requiredPaths = [
  'turbo.json',
  'pnpm-workspace.yaml',
  'README.md',
  'apps/api/pyproject.toml',
  'apps/mobile/package.json',
  'apps/admin-web/package.json',
  'packages/contracts/package.json'
];

test('monorepo scaffold baseline exists', () => {
  for (const rel of requiredPaths) {
    assert.equal(fs.existsSync(rel), true, `missing required path: ${rel}`);
  }
});

test('root scripts are wired to turbo orchestration', () => {
  const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
  const scripts = pkg.scripts || {};
  assert.match(scripts.build || '', /turbo run build/);
  assert.match(scripts.lint || '', /turbo run lint/);
  assert.match(scripts.test || '', /turbo run test/);
  assert.match(scripts.typecheck || '', /turbo run typecheck/);
});

test('workspace package scripts are executable checks (not TODO placeholders)', () => {
  const workspacePkgs = [
    'apps/mobile/package.json',
    'apps/admin-web/package.json',
    'packages/contracts/package.json'
  ];
  for (const pkgPath of workspacePkgs) {
    const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));
    const scripts = pkg.scripts || {};
    for (const key of ['build', 'lint', 'test', 'typecheck']) {
      assert.ok(scripts[key], `${pkgPath} is missing ${key} script`);
      assert.equal(
        String(scripts[key]).includes('TODO'),
        false,
        `${pkgPath} ${key} still contains TODO placeholder`
      );
    }
  }
});

test('workspace structure required by architecture exists', () => {
  const requiredDirs = ['apps', 'apps/api', 'apps/mobile', 'apps/admin-web', 'packages', 'packages/contracts'];
  for (const dir of requiredDirs) {
    assert.equal(fs.existsSync(dir), true, `missing required directory: ${dir}`);
    assert.equal(fs.statSync(dir).isDirectory(), true, `not a directory: ${dir}`);
  }
  assert.equal(fs.existsSync(path.join('apps', 'api', 'pyproject.toml')), true);
});
