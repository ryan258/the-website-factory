export async function onRequest(context) {
  const url = new URL(context.request.url);
  // Protect internal build inventory and other dotfiles from external access. /.well-known/
  // stays reachable: standard files such as security.txt and domain verification live there.
  if (url.pathname.startsWith('/.') && !url.pathname.startsWith('/.well-known/')) {
    return new Response('Not Found', {status: 404, headers: {'cache-control': 'no-store'}});
  }
  return context.next();
}
