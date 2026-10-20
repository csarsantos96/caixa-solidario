export async function apiFetch(url, options = {}) {
  const headers = new Headers(options.headers);
  if (options.method && !['GET','HEAD'].includes(options.method.toUpperCase())) {
    headers.set('X-CSRF-Protection', '1');
    headers.set('Content-Type', 'application/json');
  }
  const response = await fetch(url, {...options, headers, credentials: 'same-origin'});
  if (response.status === 401 && url !== '/api/login') window.dispatchEvent(new Event('auth-expired'));
  return response;
}
