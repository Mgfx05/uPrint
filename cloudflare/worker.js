const MAX_PDF_BYTES = 10 * 1024 * 1024;
const PDF_TTL_SECONDS = 24 * 60 * 60;

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}

function getCorsHeaders(request) {
  const origin = request.headers.get("Origin");
  return {
    "access-control-allow-origin": origin || "*",
    "access-control-allow-methods": "GET, POST, OPTIONS",
    "access-control-allow-headers": "Content-Type",
    "vary": "Origin",
  };
}

function apiJson(request, data, status = 200) {
  const headers = new Headers({
    "content-type": "application/json; charset=utf-8",
    ...getCorsHeaders(request),
  });
  return new Response(JSON.stringify(data), { status, headers });
}

function countPdfPages(bytes) {
  // Best-effort page count for ordinary PDFs. Compressed object streams may
  // require a dedicated PDF parser, which Workers do not provide natively.
  const text = new TextDecoder("latin1").decode(bytes);
  const matches = text.match(/\/Type\s*\/Page\b/g);
  return matches ? matches.length : 0;
}

function calculatePrice(pages, copies, printType, paperSize) {
  const rate = (printType === "color" ? 10 : 2) * (paperSize === "a3" ? 2 : 1);
  return { pages, copies, type: printType, paper_size: paperSize, price_per_page: rate, total_price: pages * copies * rate };
}

async function handleApi(request, env) {
  const url = new URL(request.url);
  const path = url.pathname;

  if (request.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: getCorsHeaders(request) });
  }

  if (!env.DB || !env.PDF_STORAGE) {
    return apiJson(request, { detail: "Cloudflare bindings DB and PDF_STORAGE are required." }, 500);
  }

  if (path === "/health" && request.method === "GET") {
    return apiJson(request, { status: "ok", application: "uPrint Cloud API" });
  }

  if (path === "/upload-pdf" && request.method === "POST") {
    const form = await request.formData();
    const file = form.get("file");
    if (!(file instanceof File)) return apiJson(request, { detail: "PDF file field is required." }, 400);
    if (file.size > MAX_PDF_BYTES) return apiJson(request, { detail: "File too large. Maximum size is 10 MB." }, 413);
    if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
      return apiJson(request, { detail: "Only PDF files are allowed." }, 400);
    }

    const bytes = await file.arrayBuffer();
    const signature = new TextDecoder().decode(bytes.slice(0, 5));
    if (signature !== "%PDF-") return apiJson(request, { detail: "The uploaded file is not a valid PDF." }, 400);
    const pages = countPdfPages(bytes);
    if (pages < 1) return apiJson(request, { detail: "Could not read the PDF page count. Please try saving the document as a standard PDF and upload again." }, 400);

    const fileId = crypto.randomUUID();
    await env.PDF_STORAGE.put(fileId, bytes, { expirationTtl: PDF_TTL_SECONDS });
    await env.DB.prepare(
      "INSERT INTO files (file_id, filename, page_count, file_size_bytes, created_at, expires_at) VALUES (?, ?, ?, ?, datetime('now'), datetime('now', '+24 hours'))"
    ).bind(fileId, file.name.slice(0, 255), pages, file.size).run();

    return apiJson(request, {
      message: "PDF uploaded successfully",
      file_id: fileId,
      filename: file.name,
      pages,
      file_size_bytes: file.size
    }, 201);
  }

  if (path === "/calculate-pdf-price" && request.method === "GET") {
    const fileId = url.searchParams.get("file_id");
    const copies = Number(url.searchParams.get("copies") || 1);
    const printType = url.searchParams.get("print_type") || "bw";
    const paperSize = url.searchParams.get("paper_size") || "a4";
    if (!fileId) return apiJson(request, { detail: "file_id is required." }, 400);
    if (!Number.isInteger(copies) || copies < 1 || copies > 50) return apiJson(request, { detail: "Copies must be between 1 and 50." }, 400);
    if (!["bw", "color"].includes(printType) || !["a4", "a3"].includes(paperSize)) return apiJson(request, { detail: "Invalid print options." }, 400);
    const file = await env.DB.prepare("SELECT file_id, filename, page_count FROM files WHERE file_id = ?").bind(fileId).first();
    if (!file) return apiJson(request, { detail: "PDF not found or expired." }, 404);
    return apiJson(request, { file_id: file.file_id, filename: file.filename, ...calculatePrice(file.page_count, copies, printType, paperSize) });
  }

  if (path === "/create-order" && request.method === "POST") {
    const fileId = url.searchParams.get("file_id");
    const copies = Number(url.searchParams.get("copies") || 1);
    const printType = url.searchParams.get("print_type") || "bw";
    const paperSize = url.searchParams.get("paper_size") || "a4";
    const sides = url.searchParams.get("sides") || "single";
    const orientation = url.searchParams.get("orientation") || "portrait";
    if (!fileId) return apiJson(request, { detail: "file_id is required." }, 400);
    if (!Number.isInteger(copies) || copies < 1 || copies > 50) return apiJson(request, { detail: "Copies must be between 1 and 50." }, 400);
    if (!["bw", "color"].includes(printType) || !["a4", "a3"].includes(paperSize) || !["single", "double"].includes(sides) || !["portrait", "landscape"].includes(orientation)) {
      return apiJson(request, { detail: "Invalid print options." }, 400);
    }
    const file = await env.DB.prepare("SELECT file_id, page_count FROM files WHERE file_id = ?").bind(fileId).first();
    if (!file || !(await env.PDF_STORAGE.get(fileId, { type: "arrayBuffer" }))) return apiJson(request, { detail: "PDF not found or expired. Please upload it again." }, 404);
    const pricing = calculatePrice(file.page_count, copies, printType, paperSize);
    const orderId = "UP-" + crypto.randomUUID().slice(0, 8).toUpperCase();
    await env.DB.prepare(
      "INSERT INTO orders (order_id, file_id, pages, copies, print_type, paper_size, sides, orientation, amount, payment_status, print_status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', 'queued', datetime('now'))"
    ).bind(orderId, fileId, file.page_count, copies, printType, paperSize, sides, orientation, pricing.total_price).run();
    return apiJson(request, {
      message: "Order created successfully",
      order_id: orderId,
      file_id: fileId,
      pages: file.page_count,
      copies,
      print_type: printType,
      paper_size: paperSize,
      sides,
      orientation,
      amount: pricing.total_price,
      payment_status: "pending",
      print_status: "queued"
    }, 201);
  }

  const orderMatch = path.match(/^\/order\/([A-Za-z0-9-]+)$/);
  if (orderMatch && request.method === "GET") {
    const order = await env.DB.prepare(
      "SELECT order_id, file_id, pages, copies, print_type, paper_size, sides, orientation, amount, payment_status, print_status FROM orders WHERE order_id = ?"
    ).bind(orderMatch[1]).first();
    if (!order) return apiJson(request, { detail: "Order not found." }, 404);
    return apiJson(request, { message: "Order found", ...order });
  }

  return apiJson(request, { detail: "API route not found." }, 404);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname.startsWith("/api/") || ["/health", "/upload-pdf", "/calculate-pdf-price", "/create-order"].includes(url.pathname) || url.pathname.startsWith("/order/")) {
      if (url.pathname.startsWith("/api/")) url.pathname = url.pathname.slice(4);
      return handleApi(new Request(url, request), env);
    }
    if (env.ASSETS) return env.ASSETS.fetch(request);
    return new Response("uPrint API is running. Static asset binding ASSETS is not configured.", { status: 200 });
  }
};
