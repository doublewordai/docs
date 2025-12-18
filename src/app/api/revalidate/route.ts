import {revalidateTag} from 'next/cache'
import {type NextRequest, NextResponse} from 'next/server'
import {parseBody} from 'next-sanity/webhook'

type WebhookPayload = {
  _type: string
}

/**
 * Webhook endpoint for on-demand revalidation
 *
 * Sanity will POST to this endpoint when content changes,
 * triggering revalidation of pages with matching tags
 */
export async function POST(req: NextRequest) {
  try {
    const secret = process.env.SANITY_REVALIDATE_SECRET

    if (!secret) {
      return new Response('Missing environment variable SANITY_REVALIDATE_SECRET', {
        status: 500,
      })
    }

    // Verify the webhook signature
    const {isValidSignature, body} = await parseBody<WebhookPayload>(
      req,
      secret,
    )

    if (!isValidSignature) {
      const message = 'Invalid signature'
      return new Response(JSON.stringify({message, isValidSignature, body}), {
        status: 401,
      })
    }

    if (!body?._type) {
      const message = 'Bad Request: Missing _type in webhook payload'
      return new Response(JSON.stringify({message, body}), {status: 400})
    }

    // Revalidate pages tagged with this document type
    // All client.fetch calls with {next: {tags: [body._type]}} will be revalidated
    revalidateTag(body._type, 'default')

    const message = `Revalidated tag: ${body._type}`
    console.log(message)

    return NextResponse.json({body, message})
  } catch (err: any) {
    console.error('Revalidation error:', err)
    return new Response(err.message, {status: 500})
  }
}
