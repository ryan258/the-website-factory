export async function onRequest(context) {
  const url = new URL(context.request.url);
  // Protect internal build inventory and manifest from external access
  if (url.pathname === '/.factory-build.json' || url.pathname.startsWith('/.')) {
    return new Response('Not Found', {status: 404, headers: {'cache-control': 'no-store'}});
  }
  return context.next();
}
