import { existsSync, readFileSync } from 'node:fs';

const required = [
  'README.md',
  'docs/DEVELOPER_ARSENAL.md',
  'docs/AUTOMATION_ENGINEERING_STANDARD.md',
  'docs/AI_ENGINEERING_STANDARD.md',
  'docs/PROVIDER_ADAPTER_STANDARD.md',
  'docs/CLIENT_DELIVERY_STANDARD.md',
  'docs/RECOVERY_RUNBOOK.md',
  'SECURITY.md',
];

const missing = required.filter((file) => !existsSync(file));
if (missing.length) {
  console.error(`Developer Arsenal audit failed. Missing: ${missing.join(', ')}`);
  process.exit(1);
}

const readme = readFileSync('README.md', 'utf8').toLowerCase();
for (const term of ['tenant', 'job', 'security', 'verification']) {
  if (!readme.includes(term)) {
    console.error(`Developer Arsenal audit failed. README missing concept: ${term}`);
    process.exit(1);
  }
}

console.log('Developer Arsenal audit passed.');