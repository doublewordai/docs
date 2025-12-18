import type {NextConfig} from 'next'

const nextConfig: NextConfig = {
  reactCompiler: true,

  // Enable detailed logging for cache debugging
  logging: {
    fetches: {
      fullUrl: true,
    },
  },

  // Allow images from Sanity CDN
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'cdn.sanity.io',
      },
    ],
  },
}

export default nextConfig
