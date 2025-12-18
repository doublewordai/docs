# Doubleword Documentation Site

A fully static, prerendered Next.js documentation site powered by Sanity CMS with webhook-based on-demand revalidation.

## Features

✅ **Fully Static Generation (SSG)** - All pages are prerendered at build time
✅ **Webhook-based Revalidation** - Content updates trigger automatic page revalidation
✅ **Tag-based Cache Invalidation** - Granular control over which pages to revalidate
✅ **Markdown Rendering** - Full support for GitHub-flavored markdown
✅ **Optimized Performance** - Lightning-fast page loads with Next.js 16
✅ **Type-safe** - TypeScript types for all Sanity queries

## Architecture

### Static Generation Strategy

All pages are generated at build time using Next.js `generateStaticParams`:

- **Homepage** (`/`) - Lists all products
- **Product Pages** (`/[product]`) - Product overview with documentation index
- **Documentation Pages** (`/[product]/[...slug]`) - Individual documentation pages

### Caching & Revalidation

The site uses Next.js's tag-based caching with `force-cache` strategy:

```typescript
// All pages are cached indefinitely until revalidated by webhook
cache: 'force-cache'
next: {
  revalidate: false,  // Cache indefinitely
  tags: ['product', 'docPage', 'category']  // Tags for invalidation
}
```

When content changes in Sanity:
1. Sanity sends a webhook to `/api/revalidate`
2. The API validates the request signature
3. `revalidateTag()` is called with the document type
4. All pages with that tag are purged from cache
5. Next request rebuilds the page with fresh content

## Setup

### 1. Environment Variables

Update `.env.local` with your values:

```bash
NEXT_PUBLIC_SANITY_PROJECT_ID=g1zo7y59
NEXT_PUBLIC_SANITY_DATASET=production
SANITY_REVALIDATE_SECRET=your-secret-here-change-me
```

⚠️ **Important**: Generate a secure random string for `SANITY_REVALIDATE_SECRET`

### 2. Install Dependencies

```bash
npm install
```

### 3. Configure Sanity Webhook

To enable automatic revalidation when content changes:

1. Go to [Sanity Manage](https://www.sanity.io/manage)
2. Select your project
3. Go to **API** → **Webhooks**
4. Click **Create webhook**
5. Configure:
   - **Name**: Next.js Revalidation
   - **URL**: `https://your-domain.com/api/revalidate`
   - **Method**: POST
   - **Secret**: Use the same value as `SANITY_REVALIDATE_SECRET`
   - **Trigger on**: Create, Update, Delete
   - **Dataset**: production
   - **Projection**: `{_type}`

Example projection:
```groq
{
  _type
}
```

This sends the document type to your API route, which revalidates all pages with that tag.

### 4. Deploy

The site works with any hosting provider that supports Next.js:

#### Vercel (Recommended)
```bash
vercel deploy
```

Add environment variables in Vercel dashboard.

#### Other Platforms
```bash
npm run build
npm start
```

Ensure your hosting provider:
- Supports Next.js 16+
- Has environment variables configured
- Can receive webhook requests

## Development

### Run Dev Server
```bash
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000)

### Build for Production
```bash
npm run build
```

This generates all static pages. Check the build output:
```
Route (app)
├ ○ /                          (Static)
├ ● /[product]                 (SSG) - 3 routes
├ ● /[product]/[...slug]       (SSG) - 20 routes
└ ƒ /api/revalidate            (Dynamic)
```

- `○` = Static prerendered content
- `●` = SSG with `generateStaticParams`
- `ƒ` = Dynamic API route

## Project Structure

```
docs-new/
├── src/
│   ├── app/
│   │   ├── page.tsx                    # Homepage
│   │   ├── [product]/
│   │   │   ├── page.tsx               # Product landing page
│   │   │   └── [...slug]/
│   │   │       └── page.tsx           # Documentation pages
│   │   └── api/
│   │       └── revalidate/
│   │           └── route.ts           # Webhook handler
│   ├── components/
│   │   └── MarkdownRenderer.tsx       # Markdown rendering
│   └── sanity/
│       ├── env.ts                      # Environment config
│       ├── types.ts                    # TypeScript types
│       └── lib/
│           ├── client.ts               # Sanity client
│           └── queries.ts              # GROQ queries
├── .env.local                          # Environment variables
├── next.config.ts                      # Next.js config
└── package.json
```

## Sanity Schema

The site expects these document types in your Sanity schema:

### `product`
- `name` (string)
- `slug` (slug)
- `description` (text)
- `githubUrl` (url)
- `icon` (image)

### `docPage`
- `title` (string)
- `slug` (slug)
- `product` (reference → product)
- `category` (reference → category)
- `body` (markdown)
- `order` (number)
- `parent` (reference → docPage)
- `description` (text)
- `sidebarLabel` (string)
- `hideTitle` (boolean)

### `category`
- `name` (string)
- `slug` (slug)
- `product` (reference → product)
- `order` (number)
- `parent` (reference → category)
- `description` (text)

## Best Practices

### Static Site Generation
- `useCdn: false` in Sanity client (for consistent builds)
- `cache: 'force-cache'` for all data fetches
- Tags on every query for granular revalidation

### Performance
- All pages prerendered at build time
- Optimized markdown rendering
- Image optimization via Next.js Image component

### Debugging Cache
The `logging.fetches.fullUrl` config in `next.config.ts` shows detailed cache information:

```bash
npm run dev
```

You'll see logs like:
```
GET https://g1zo7y59.api.sanity.io/v2024-07-11/data/query/production?query=...
cache: HIT
tags: ['product']
```

## Troubleshooting

### Pages not updating after content change
1. Check webhook is configured correctly in Sanity
2. Verify `SANITY_REVALIDATE_SECRET` matches in both places
3. Check webhook logs in Sanity dashboard
4. Test webhook endpoint manually:

```bash
curl -X POST https://your-domain.com/api/revalidate \
  -H "Content-Type: application/json" \
  -H "Sanity-Webhook-Signature: your-signature" \
  -d '{"_type": "docPage"}'
```

### Build fails with "not found"
- Ensure all referenced documents exist in Sanity
- Check GROQ queries return expected data
- Verify `generateStaticParams` returns correct paths

### Slow builds
- Reduce number of static pages with pagination
- Use incremental static regeneration (ISR) for less critical pages
- Consider on-demand generation for rarely accessed pages

## Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [Sanity Documentation](https://www.sanity.io/docs)
- [next-sanity Toolkit](https://github.com/sanity-io/next-sanity)
- [GROQ Query Language](https://www.sanity.io/docs/groq)
