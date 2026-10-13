// Bound static transport before decoding. This does not compute scientific results.
export async function readBoundedBytes(response, maximum) {
  if (!Number.isInteger(maximum) || maximum < 1)
    throw new Error("Invalid limit");
  const advertised = response.headers.get("content-length");
  if (
    advertised !== null &&
    (!/^\d+$/.test(advertised) || Number(advertised) > maximum)
  ) {
    await response.body?.cancel();
    throw new Error("Oversized or invalid content length");
  }
  if (!response.body) throw new Error("Missing static response body");
  const reader = response.body.getReader();
  const chunks = [];
  let size = 0;
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      if (!(value instanceof Uint8Array) || value.byteLength > maximum - size) {
        throw new Error("Oversized static response");
      }
      size += value.byteLength;
      chunks.push(value);
    }
    const result = new Uint8Array(size);
    let offset = 0;
    for (const chunk of chunks) {
      result.set(chunk, offset);
      offset += chunk.length;
    }
    return result;
  } finally {
    await reader.cancel();
    reader.releaseLock();
  }
}
