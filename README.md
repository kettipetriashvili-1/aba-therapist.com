# Keti Petriashvili — Psychologist

A multilingual Hugo website for English-language ABA support and professional outreach.

## Local development

```bash
hugo server --disableFastRender
```

Production-equivalent build:

```bash
hugo --gc --minify --panicOnWarning --cleanDestinationDir
```

## Cloudflare Pages

- Production branch: `main`
- Build command: `hugo --gc --minify`
- Build output directory: `public`
- Primary domain: `aba-therapist.com`

Set `HUGO_VERSION` in Cloudflare Pages to the tested Hugo version recorded in `hugo.toml` project history when deployment is configured.

## Publication blockers

Before the first public deployment:

1. Have Keti approve the generated hero and About-page imagery, or replace it with approved real photography.
2. Keep case examples unpublished, as Keti requested. Add testimonials only after receiving approved wording and permission; no approved testimonials have been supplied.
3. Check credential documents and current status before public launch. Education and credential award dates currently come from Keti’s supplied CV; no certificate scans are published.
4. Finalize the legal/privacy page with the operator’s real jurisdiction, address, registration information and a qualified review.
5. The public contact email is confirmed as `info@aba-therapist.com`.
6. Have Keti review the English professional claims and all translated terminology.

## English copy sources

The homepage and first-person About page use Keti’s supplied CV (`keti1.pdf`) and questionnaire answers (`keti2.docx`). The original files remain outside the repository in QubesIncoming; their private contact details are not published. The CV supplies professional history and award dates, not independent verification of current credential status.

Composite cases and fictional testimonials have been removed. The existing positive-reinforcement article remains an explicitly labelled, noindex layout example awaiting Keti’s review, not an approved article attributed to her. Legal/privacy details still require completion. Translations remain disabled until the English copy is approved.
