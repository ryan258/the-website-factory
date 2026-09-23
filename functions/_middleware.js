export async function onRequest(context) {
  const url = new URL(context.request.url);
  // Hide the build manifest and other dotfiles. /.well-known/ is a public standard
  // (security.txt, domain verification), so it stays reachable.
  if (url.pathname.startsWith('/.') && !url.pathname.startsWith('/.well-known/')) {
    return new Response('Not Found', {status: 404, headers: {'cache-control': 'no-store'}});
  }
  return context.next();
}
