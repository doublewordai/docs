import Link from 'next/link'
import {sanityFetch} from '@/sanity/lib/client'
import {PRODUCTS_QUERY} from '@/sanity/lib/queries'
import type {Product} from '@/sanity/types'

export default async function HomePage() {
  const products = await sanityFetch({
    query: PRODUCTS_QUERY,
    // Tag for on-demand revalidation via webhook
    tags: ['product'],
  }) as Product[]

  return (
    <div className="min-h-screen max-w-6xl mx-auto px-8 py-16">
      <header className="mb-12">
        <h1 className="text-5xl font-bold mb-4">Doubleword Documentation</h1>
        <p className="text-xl text-gray-600">
          Explore documentation for our open-source projects and APIs
        </p>
      </header>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
        {products?.map((product) => (
          <Link
            key={product._id}
            href={`/${product.slug.current}`}
            className="p-6 border border-gray-200 rounded-lg hover:border-gray-400 hover:shadow-lg transition-all"
          >
            <h2 className="text-2xl font-semibold mb-2">{product.name}</h2>
            {product.description && (
              <p className="text-gray-600">{product.description}</p>
            )}
          </Link>
        ))}
      </div>
    </div>
  )
}
